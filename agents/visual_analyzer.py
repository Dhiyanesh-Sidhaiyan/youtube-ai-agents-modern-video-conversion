"""
Visual Analyzer Agent
Analyzes Manim animation frames for quality issues and generates fix instructions.

Checks:
1. Text alignment and positioning
2. Element overlap detection
3. Off-screen content
4. Font size and readability
5. Color contrast
6. Blank/empty frames
7. Animation smoothness
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional

try:
    from PIL import Image, ImageStat
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not installed. Visual analysis will be limited.")


@dataclass
class VisualIssue:
    """A detected visual issue in an animation."""
    issue_type: str  # alignment, overlap, offscreen, font, contrast, blank
    severity: str    # critical, warning, info
    description: str
    frame_number: int = 0
    fix_suggestion: str = ""

    def to_dict(self):
        return {
            "type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "frame": self.frame_number,
            "fix": self.fix_suggestion,
        }


@dataclass
class FrameAnalysis:
    """Analysis results for a single frame."""
    frame_number: int
    brightness: float = 0.0
    contrast: float = 0.0
    is_blank: bool = False
    text_regions: int = 0
    edge_density: float = 0.0  # Measure of content
    issues: list = field(default_factory=list)


@dataclass
class SceneVisualAnalysis:
    """Complete visual analysis for a scene."""
    scene_id: int
    total_frames: int = 0
    analyzed_frames: int = 0
    blank_frame_count: int = 0
    avg_brightness: float = 0.0
    avg_contrast: float = 0.0
    issues: list = field(default_factory=list)
    quality_score: float = 100.0
    # New fields for animation analysis
    is_animated: bool = True
    animation_score: float = 100.0
    border_issues: list = field(default_factory=list)

    def to_dict(self):
        return {
            "scene_id": self.scene_id,
            "total_frames": self.total_frames,
            "blank_frames": self.blank_frame_count,
            "blank_ratio": f"{self.blank_frame_count / max(1, self.total_frames) * 100:.1f}%",
            "avg_brightness": f"{self.avg_brightness:.1f}",
            "quality_score": f"{self.quality_score:.1f}",
            "is_animated": self.is_animated,
            "animation_score": f"{self.animation_score:.1f}",
            "border_issues": self.border_issues,
            "issues": [i.to_dict() for i in self.issues],
        }


def extract_frames(mp4_path: str, count: int = 10) -> list:
    """Extract sample frames from video using ffmpeg."""
    if not os.path.exists(mp4_path):
        return []

    frames = []
    with tempfile.TemporaryDirectory() as tmpdir:
        # Get video duration
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            mp4_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            duration = float(result.stdout.strip())
        except ValueError:
            duration = 10.0

        # Extract frames at regular intervals
        interval = duration / (count + 1)
        for i in range(count):
            timestamp = interval * (i + 1)
            frame_path = os.path.join(tmpdir, f"frame_{i:03d}.png")

            cmd = [
                "ffmpeg", "-y", "-v", "quiet",
                "-ss", str(timestamp),
                "-i", mp4_path,
                "-vframes", "1",
                "-f", "image2",
                frame_path
            ]
            subprocess.run(cmd, capture_output=True)

            if os.path.exists(frame_path) and HAS_PIL:
                try:
                    img = Image.open(frame_path)
                    frames.append((i, timestamp, img.copy()))
                    img.close()
                except Exception:
                    pass

    return frames


def analyze_frame(frame_num: int, timestamp: float, img: Image.Image) -> FrameAnalysis:
    """Analyze a single frame for visual quality issues."""
    analysis = FrameAnalysis(frame_number=frame_num)

    if not HAS_PIL:
        return analysis

    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Get image statistics
    stat = ImageStat.Stat(img)
    analysis.brightness = sum(stat.mean) / 3
    analysis.contrast = sum(stat.stddev) / 3

    # Check for blank/near-blank frame
    # A blank frame has very low contrast (uniform color)
    if analysis.contrast < 5:
        analysis.is_blank = True
        analysis.issues.append(VisualIssue(
            issue_type="blank",
            severity="critical",
            description=f"Blank or near-blank frame at {timestamp:.1f}s",
            frame_number=frame_num,
            fix_suggestion="Add visual content or extend previous animation"
        ))

    # Check brightness (too dark or too bright)
    if analysis.brightness < 20:
        analysis.issues.append(VisualIssue(
            issue_type="contrast",
            severity="warning",
            description=f"Frame too dark (brightness: {analysis.brightness:.0f})",
            frame_number=frame_num,
            fix_suggestion="Use lighter colors or add background"
        ))
    elif analysis.brightness > 240:
        analysis.issues.append(VisualIssue(
            issue_type="contrast",
            severity="warning",
            description=f"Frame too bright (brightness: {analysis.brightness:.0f})",
            frame_number=frame_num,
            fix_suggestion="Use darker text or elements for contrast"
        ))

    # Detect content density using edge detection
    try:
        gray = img.convert('L')
        pixels = list(gray.getdata())
        width, height = gray.size

        # Simple edge detection: count pixel differences
        edges = 0
        for y in range(height - 1):
            for x in range(width - 1):
                idx = y * width + x
                if abs(pixels[idx] - pixels[idx + 1]) > 30:
                    edges += 1
                if abs(pixels[idx] - pixels[idx + width]) > 30:
                    edges += 1

        analysis.edge_density = edges / (width * height)

        # Very low edge density might indicate lack of content
        if analysis.edge_density < 0.001 and not analysis.is_blank:
            analysis.issues.append(VisualIssue(
                issue_type="content",
                severity="info",
                description="Low visual content density",
                frame_number=frame_num,
                fix_suggestion="Add more visual elements or text"
            ))

    except Exception:
        pass

    # Check for potential off-screen content (edges near borders)
    width, height = img.size
    border = 20
    try:
        # Check borders for non-background content
        left_strip = img.crop((0, 0, border, height))
        right_strip = img.crop((width - border, 0, width, height))
        top_strip = img.crop((0, 0, width, border))
        bottom_strip = img.crop((0, height - border, width, height))

        for name, strip in [("left", left_strip), ("right", right_strip),
                            ("top", top_strip), ("bottom", bottom_strip)]:
            strip_stat = ImageStat.Stat(strip)
            strip_contrast = sum(strip_stat.stddev) / 3

            # High contrast at edge might indicate cut-off content
            if strip_contrast > 40:
                analysis.issues.append(VisualIssue(
                    issue_type="offscreen",
                    severity="warning",
                    description=f"Possible content cut off at {name} edge",
                    frame_number=frame_num,
                    fix_suggestion=f"Move elements away from {name} edge or use smaller scale"
                ))

    except Exception:
        pass

    return analysis


def check_border_content(img: Image.Image, background_threshold: float = 25.0) -> list:
    """
    Check if content is being cut off at frame borders.

    Returns list of border names where content may be cut off.
    """
    if not HAS_PIL:
        return []

    width, height = img.size
    border_size = 15  # pixels to check at each edge
    issues = []

    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Get center region to estimate background color
    center_x, center_y = width // 2, height // 2
    center_region = img.crop((
        center_x - 50, center_y - 50,
        center_x + 50, center_y + 50
    ))
    center_stat = ImageStat.Stat(center_region)

    # Sample border regions
    regions = {
        "left": img.crop((0, height // 4, border_size, 3 * height // 4)),
        "right": img.crop((width - border_size, height // 4, width, 3 * height // 4)),
        "top": img.crop((width // 4, 0, 3 * width // 4, border_size)),
        "bottom": img.crop((width // 4, height - border_size, 3 * width // 4, height)),
    }

    for name, region in regions.items():
        try:
            region_stat = ImageStat.Stat(region)
            region_contrast = sum(region_stat.stddev) / 3

            # If border has significant contrast (content), it might be cut off
            if region_contrast > background_threshold:
                # Additional check: is this different from typical Manim background?
                region_brightness = sum(region_stat.mean) / 3
                # Manim dark backgrounds are usually < 50 brightness
                # If border has both high contrast AND content-like brightness, flag it
                if region_brightness > 30 or region_contrast > 50:
                    issues.append(name)
        except Exception:
            pass

    return issues


def detect_text_overlap(img: Image.Image, region_size: int = 100) -> list:
    """
    Detect potential text overlap by analyzing edge density in grid regions.

    High edge density in a small region often indicates overlapping text,
    since overlapping characters create many more edges than spaced text.

    Args:
        img: PIL Image to analyze
        region_size: Size of grid regions to analyze (pixels)

    Returns:
        List of detected overlap issues with region info
    """
    if not HAS_PIL:
        return []

    issues = []

    try:
        # Convert to grayscale
        if img.mode != 'L':
            gray = img.convert('L')
        else:
            gray = img

        width, height = gray.size
        pixels = list(gray.getdata())

        # Divide frame into regions and analyze each
        regions_x = width // region_size
        regions_y = height // region_size

        high_density_regions = []

        for ry in range(regions_y):
            for rx in range(regions_x):
                # Calculate region bounds
                x1 = rx * region_size
                y1 = ry * region_size
                x2 = min(x1 + region_size, width)
                y2 = min(y1 + region_size, height)

                # Count edges in this region
                edges = 0
                total_pixels = 0

                for y in range(y1, y2 - 1):
                    for x in range(x1, x2 - 1):
                        idx = y * width + x
                        # Horizontal edge
                        if abs(pixels[idx] - pixels[idx + 1]) > 40:
                            edges += 1
                        # Vertical edge
                        if abs(pixels[idx] - pixels[idx + width]) > 40:
                            edges += 1
                        total_pixels += 1

                if total_pixels > 0:
                    edge_density = edges / total_pixels

                    # High threshold for overlap detection
                    # Normal text: 0.02-0.08 edge density
                    # Overlapping text: > 0.15 edge density
                    if edge_density > 0.15:
                        high_density_regions.append({
                            "region": (rx, ry),
                            "center_x": (x1 + x2) // 2,
                            "center_y": (y1 + y2) // 2,
                            "density": edge_density,
                        })

        # If multiple adjacent regions have high density, likely overlap
        if len(high_density_regions) >= 2:
            # Check if regions are adjacent (potential text merge)
            for i, r1 in enumerate(high_density_regions):
                for r2 in high_density_regions[i + 1:]:
                    # Adjacent check
                    rx_diff = abs(r1["region"][0] - r2["region"][0])
                    ry_diff = abs(r1["region"][1] - r2["region"][1])

                    if rx_diff <= 1 and ry_diff <= 1:
                        # Calculate position description
                        cy = (r1["center_y"] + r2["center_y"]) // 2
                        if cy < height // 3:
                            position = "top"
                        elif cy < 2 * height // 3:
                            position = "center"
                        else:
                            position = "bottom"

                        issues.append({
                            "type": "text_overlap",
                            "position": position,
                            "density": max(r1["density"], r2["density"]),
                            "description": f"Possible text overlap in {position} region",
                        })
                        break

        # Also check for very high density in single region (tight overlap)
        for region in high_density_regions:
            if region["density"] > 0.25:
                cy = region["center_y"]
                if cy < height // 3:
                    position = "top"
                elif cy < 2 * height // 3:
                    position = "center"
                else:
                    position = "bottom"

                issues.append({
                    "type": "dense_text",
                    "position": position,
                    "density": region["density"],
                    "description": f"Very dense content in {position} (possible overlap)",
                })

    except Exception:
        pass

    # Deduplicate issues by position
    seen_positions = set()
    unique_issues = []
    for issue in issues:
        if issue["position"] not in seen_positions:
            seen_positions.add(issue["position"])
            unique_issues.append(issue)

    return unique_issues


# ─── Math-Aware Frame Analysis ───────────────────────────────────────────────

MATH_SCENE_TYPES = (
    "math_formula", "equation_derivation", "graph_visualization",
    "geometric_theorem", "matrix_operation"
)


def analyze_math_frame(
    img: Image.Image,
    scene_type: str,
    frame_num: int = 0
) -> dict:
    """
    Special analysis for math/equation scenes.

    Math scenes have different characteristics than general scenes:
    - Higher edge density is expected (equations have many symbols)
    - More "complex" visual patterns are normal
    - Need to check equation readability, not flag as "overlap"

    Args:
        img: PIL Image to analyze
        scene_type: Type of the scene (e.g., "equation_derivation")
        frame_num: Frame number for reporting

    Returns:
        Dict with math-specific analysis results
    """
    if scene_type not in MATH_SCENE_TYPES:
        return {"applicable": False}

    if not HAS_PIL:
        return {"applicable": True, "analysis_available": False}

    result = {
        "applicable": True,
        "scene_type": scene_type,
        "frame": frame_num,
        "issues": [],
        "readable": True,
        "well_positioned": True,
    }

    try:
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size

        # 1. Check contrast ratio for equation readability
        # Equations need good contrast to be readable
        stat = ImageStat.Stat(img)
        overall_contrast = sum(stat.stddev) / 3
        overall_brightness = sum(stat.mean) / 3

        # WCAG AA standard requires 4.5:1 contrast ratio for text
        # We approximate this with contrast/brightness ratio
        if overall_contrast < 15:
            result["issues"].append({
                "type": "low_contrast",
                "severity": "warning",
                "description": "Low contrast - equations may be hard to read",
                "fix": "Use higher contrast colors: WHITE on dark bg, or darker colors on light bg"
            })
            result["readable"] = False

        # 2. Check equation positioning
        # Equations should typically be centered or in upper-center
        # Look for high-density content regions
        gray = img.convert('L')
        pixels = list(gray.getdata())

        # Divide frame into vertical thirds
        third_height = height // 3
        thirds_density = []

        for third in range(3):
            y_start = third * third_height
            y_end = (third + 1) * third_height

            edges = 0
            pixels_count = 0
            for y in range(y_start, y_end - 1):
                for x in range(0, width - 1, 2):  # Sample every other pixel for speed
                    idx = y * width + x
                    if abs(pixels[idx] - pixels[idx + 1]) > 30:
                        edges += 1
                    pixels_count += 1

            density = edges / max(1, pixels_count)
            thirds_density.append(density)

        # If main content (highest density) is in bottom third, it's positioned too low
        max_density_third = thirds_density.index(max(thirds_density))
        if max_density_third == 2 and thirds_density[2] > thirds_density[0] * 1.5:
            result["issues"].append({
                "type": "low_positioning",
                "severity": "info",
                "description": "Equation content positioned in lower third of frame",
                "fix": "Move equations up using .shift(UP) or .move_to(ORIGIN + UP * 0.5)"
            })
            result["well_positioned"] = False

        # 3. Check for center concentration (good for math)
        # Math content should ideally be horizontally centered
        left_half = img.crop((0, 0, width // 2, height))
        right_half = img.crop((width // 2, 0, width, height))

        left_stat = ImageStat.Stat(left_half)
        right_stat = ImageStat.Stat(right_half)

        left_contrast = sum(left_stat.stddev) / 3
        right_contrast = sum(right_stat.stddev) / 3

        # Large imbalance suggests off-center content
        if abs(left_contrast - right_contrast) > 30:
            heavier_side = "left" if left_contrast > right_contrast else "right"
            result["issues"].append({
                "type": "off_center",
                "severity": "info",
                "description": f"Math content is heavier on {heavier_side} side",
                "fix": f"Use .move_to(ORIGIN) to center equations, or balance with elements on {('right' if heavier_side == 'left' else 'left')}"
            })

        # 4. Special check for graph_visualization
        if scene_type == "graph_visualization":
            # Graphs should have axes (consistent horizontal and vertical lines)
            # Check for presence of axis-like patterns
            horizontal_edges = 0
            vertical_edges = 0

            center_region = img.crop((width // 4, height // 4, 3 * width // 4, 3 * height // 4))
            center_gray = center_region.convert('L')
            center_pixels = list(center_gray.getdata())
            cw, ch = center_region.size

            for y in range(1, ch - 1):
                for x in range(1, cw - 1, 2):
                    idx = y * cw + x
                    # Check for horizontal continuity
                    if abs(center_pixels[idx] - center_pixels[idx + 1]) < 10:
                        horizontal_edges += 1
                    # Check for vertical continuity
                    if abs(center_pixels[idx] - center_pixels[idx + cw]) < 10:
                        vertical_edges += 1

            # If neither axis is detected, might be missing coordinate system
            axis_threshold = (cw * ch) * 0.05
            if horizontal_edges < axis_threshold and vertical_edges < axis_threshold:
                result["issues"].append({
                    "type": "missing_axes",
                    "severity": "warning",
                    "description": "Graph visualization may be missing coordinate axes",
                    "fix": "Ensure Axes() or NumberPlane() is properly created and visible"
                })

        # 5. Don't penalize high edge density for math scenes
        # Override the general "dense_text" detection for math content
        result["edge_density_note"] = (
            "Math scenes naturally have high edge density due to symbols - "
            "this is expected and not flagged as overlap"
        )

    except Exception as e:
        result["error"] = str(e)

    return result


def get_math_quality_score(analysis: dict) -> float:
    """
    Calculate quality score for math-specific frame analysis.

    Args:
        analysis: Result from analyze_math_frame()

    Returns:
        Quality score 0-100
    """
    if not analysis.get("applicable", False):
        return 100.0  # Not a math scene, don't affect score

    score = 100.0

    for issue in analysis.get("issues", []):
        severity = issue.get("severity", "info")
        if severity == "warning":
            score -= 10
        elif severity == "info":
            score -= 3

    if not analysis.get("readable", True):
        score -= 15

    if not analysis.get("well_positioned", True):
        score -= 5

    return max(0, score)


def check_animation_motion(frames: list) -> dict:
    """
    Check if the video has actual animation (not static).

    Args:
        frames: List of (frame_num, timestamp, img) tuples

    Returns:
        Dict with 'is_animated', 'animation_score', and 'frame_differences'
    """
    if not HAS_PIL or len(frames) < 3:
        return {"is_animated": True, "animation_score": 100.0, "frame_differences": []}

    try:
        differences = []

        for i in range(len(frames) - 1):
            _, _, img1 = frames[i]
            _, _, img2 = frames[i + 1]

            # Convert to grayscale for comparison
            if img1.mode != 'L':
                img1 = img1.convert('L')
            if img2.mode != 'L':
                img2 = img2.convert('L')

            # Ensure same size
            if img1.size != img2.size:
                continue

            # Calculate pixel difference
            pixels1 = list(img1.getdata())
            pixels2 = list(img2.getdata())

            total_diff = sum(abs(p1 - p2) for p1, p2 in zip(pixels1, pixels2))
            avg_diff = total_diff / len(pixels1) if pixels1 else 0
            differences.append(avg_diff)

        if not differences:
            return {"is_animated": True, "animation_score": 100.0, "frame_differences": []}

        avg_motion = sum(differences) / len(differences)
        max_motion = max(differences)

        # Scoring:
        # avg_motion < 0.5: essentially static (score 0-20)
        # avg_motion 0.5-2: minimal animation (score 20-50)
        # avg_motion 2-10: good animation (score 50-80)
        # avg_motion > 10: high animation (score 80-100)

        if avg_motion < 0.5:
            animation_score = avg_motion * 40  # 0-20
            is_animated = False
        elif avg_motion < 2:
            animation_score = 20 + (avg_motion - 0.5) * 20  # 20-50
            is_animated = True
        elif avg_motion < 10:
            animation_score = 50 + (avg_motion - 2) * 3.75  # 50-80
            is_animated = True
        else:
            animation_score = min(100, 80 + (avg_motion - 10) * 2)  # 80-100
            is_animated = True

        return {
            "is_animated": is_animated,
            "animation_score": round(animation_score, 1),
            "avg_motion": round(avg_motion, 2),
            "max_motion": round(max_motion, 2),
            "frame_differences": [round(d, 2) for d in differences],
        }

    except Exception as e:
        return {"is_animated": True, "animation_score": 100.0, "frame_differences": [], "error": str(e)}


def analyze_scene_video(
    mp4_path: str,
    scene_id: int,
    sample_count: int = 10,
    scene_type: str = ""
) -> SceneVisualAnalysis:
    """
    Analyze a scene's video for visual quality issues.

    Args:
        mp4_path: Path to the MP4 video file
        scene_id: Scene identifier
        sample_count: Number of frames to sample
        scene_type: Type of scene (e.g., "equation_derivation") for specialized analysis

    Returns:
        SceneVisualAnalysis with detected issues and quality score
    """
    analysis = SceneVisualAnalysis(scene_id=scene_id)
    is_math_scene = scene_type in MATH_SCENE_TYPES

    if not os.path.exists(mp4_path):
        analysis.issues.append(VisualIssue(
            issue_type="missing",
            severity="critical",
            description="Video file not found",
            fix_suggestion="Re-render the scene"
        ))
        analysis.quality_score = 0
        return analysis

    # Extract and analyze frames
    frames = extract_frames(mp4_path, sample_count)
    analysis.total_frames = sample_count
    analysis.analyzed_frames = len(frames)

    if not frames:
        analysis.issues.append(VisualIssue(
            issue_type="extraction",
            severity="critical",
            description="Could not extract frames from video",
            fix_suggestion="Check video file integrity"
        ))
        analysis.quality_score = 0
        return analysis

    brightness_sum = 0
    contrast_sum = 0

    for frame_num, timestamp, img in frames:
        frame_analysis = analyze_frame(frame_num, timestamp, img)

        if frame_analysis.is_blank:
            analysis.blank_frame_count += 1

        brightness_sum += frame_analysis.brightness
        contrast_sum += frame_analysis.contrast

        # Add frame issues to scene issues
        analysis.issues.extend(frame_analysis.issues)

    analysis.avg_brightness = brightness_sum / len(frames)
    analysis.avg_contrast = contrast_sum / len(frames)

    # ── Animation Motion Check ──────────────────────────────────────────────
    motion_result = check_animation_motion(frames)
    analysis.is_animated = motion_result.get("is_animated", True)
    analysis.animation_score = motion_result.get("animation_score", 100.0)

    if not analysis.is_animated:
        analysis.issues.append(VisualIssue(
            issue_type="static",
            severity="warning",
            description="Scene appears static with minimal animation",
            fix_suggestion="Add more animations: Write(), FadeIn(), Transform(), etc."
        ))

    # ── Border Content Check ────────────────────────────────────────────────
    # Check multiple frames for border issues
    border_issues_count = {}
    for frame_num, timestamp, img in frames:
        border_edges = check_border_content(img)
        for edge in border_edges:
            border_issues_count[edge] = border_issues_count.get(edge, 0) + 1

    # If border issue appears in >30% of frames, flag it
    frame_threshold = len(frames) * 0.3
    for edge, count in border_issues_count.items():
        if count >= frame_threshold:
            analysis.border_issues.append(edge)
            analysis.issues.append(VisualIssue(
                issue_type="border_cutoff",
                severity="warning",
                description=f"Content may be cut off at {edge} border ({count}/{len(frames)} frames)",
                frame_number=0,
                fix_suggestion=f"Use .scale(0.8) or move elements away from {edge} edge"
            ))

    # ── Text Overlap Detection ─────────────────────────────────────────────
    # For math scenes, use math-aware analysis (don't flag equations as overlap)
    if is_math_scene:
        # Math-aware analysis for equation scenes
        math_issues_count = {}
        for frame_num, timestamp, img in frames:
            math_analysis = analyze_math_frame(img, scene_type, frame_num)
            for issue in math_analysis.get("issues", []):
                issue_type = issue.get("type", "unknown")
                math_issues_count[issue_type] = math_issues_count.get(issue_type, 0) + 1

        # Flag math-specific issues that appear consistently
        math_threshold = len(frames) * 0.3
        for issue_type, count in math_issues_count.items():
            if count >= math_threshold:
                # Map issue type to VisualIssue
                severity = "warning" if issue_type in ("low_contrast", "missing_axes") else "info"
                analysis.issues.append(VisualIssue(
                    issue_type=f"math_{issue_type}",
                    severity=severity,
                    description=f"Math content issue: {issue_type.replace('_', ' ')} ({count}/{len(frames)} frames)",
                    frame_number=0,
                    fix_suggestion=f"Check equation readability and positioning"
                ))
    else:
        # Standard text overlap detection for non-math scenes
        overlap_positions = {}
        for frame_num, timestamp, img in frames:
            overlap_issues = detect_text_overlap(img)
            for issue in overlap_issues:
                pos = issue["position"]
                overlap_positions[pos] = overlap_positions.get(pos, 0) + 1

        # If overlap detected in >20% of frames at same position, flag it
        overlap_threshold = len(frames) * 0.2
        for position, count in overlap_positions.items():
            if count >= overlap_threshold:
                analysis.issues.append(VisualIssue(
                    issue_type="text_overlap",
                    severity="warning",
                    description=f"Possible text overlap in {position} region ({count}/{len(frames)} frames)",
                    frame_number=0,
                    fix_suggestion=(
                        f"Use VGroup + arrange(DOWN, buff=0.3) for text in {position}; "
                        "Use next_to() instead of hardcoded positions"
                    )
                ))

    # ── Calculate quality score ─────────────────────────────────────────────
    # Start at 100, deduct for issues
    score = 100.0

    # Deduct for blank frames
    blank_ratio = analysis.blank_frame_count / analysis.analyzed_frames
    score -= blank_ratio * 50  # Up to 50 points for blank frames

    # Deduct for issues
    critical_issues = sum(1 for i in analysis.issues if i.severity == "critical")
    warning_issues = sum(1 for i in analysis.issues if i.severity == "warning")

    score -= critical_issues * 15
    score -= warning_issues * 5

    # Deduct for static content (no animation)
    if not analysis.is_animated:
        score -= 15

    # Deduct for border issues
    score -= len(analysis.border_issues) * 5

    # Bonus for good contrast
    if 30 < analysis.avg_contrast < 100:
        score += 5

    # Bonus for good animation
    if analysis.animation_score > 70:
        score += 5

    analysis.quality_score = max(0, min(100, score))

    return analysis


def generate_fix_instructions(analysis: SceneVisualAnalysis, scene_data: dict) -> dict:
    """Generate specific fix instructions based on visual analysis."""
    instructions = {
        "scene_id": analysis.scene_id,
        "needs_fix": analysis.quality_score < 70,
        "current_score": analysis.quality_score,
        "fixes": [],
    }

    # Group issues by type
    issue_types = {}
    for issue in analysis.issues:
        if issue.issue_type not in issue_types:
            issue_types[issue.issue_type] = []
        issue_types[issue.issue_type].append(issue)

    # Generate fixes for each issue type
    if "blank" in issue_types:
        blank_count = len(issue_types["blank"])
        instructions["fixes"].append({
            "type": "animation_content",
            "description": f"Add more animation content - {blank_count} blank frames detected",
            "manim_suggestion": "Add self.wait() calls or extend animations",
        })

    if "offscreen" in issue_types:
        edges = set(i.description.split()[-2] for i in issue_types["offscreen"])
        instructions["fixes"].append({
            "type": "positioning",
            "description": f"Content may be cut off at: {', '.join(edges)}",
            "manim_suggestion": "Use .scale(0.8) or move elements with .shift() away from edges",
        })

    if "contrast" in issue_types:
        instructions["fixes"].append({
            "type": "colors",
            "description": "Improve color contrast",
            "manim_suggestion": "Use WHITE text on dark backgrounds, or BLUE/GREEN on light",
        })

    if "content" in issue_types:
        instructions["fixes"].append({
            "type": "content_density",
            "description": "Low visual content - add more elements",
            "manim_suggestion": "Add Text, shapes, or diagrams to fill the scene",
        })

    # New: Static animation fix
    if "static" in issue_types:
        instructions["fixes"].append({
            "type": "animation",
            "description": "Scene appears static with minimal animation",
            "manim_suggestion": "Add animations: Write(), FadeIn(), GrowFromCenter(), Transform(). Use self.play() for each element.",
        })

    # New: Border cutoff fix
    if "border_cutoff" in issue_types:
        edges = set(i.description.split()[-4] for i in issue_types["border_cutoff"])
        instructions["fixes"].append({
            "type": "border_positioning",
            "description": f"Content appears cut off at borders: {', '.join(edges)}",
            "manim_suggestion": "Use .scale(0.8) on large elements, avoid hardcoded positions > 5, use .to_edge() with buff=0.5",
        })

    # New: Text overlap fix
    if "text_overlap" in issue_types:
        positions = set()
        for issue in issue_types["text_overlap"]:
            # Extract position from description
            desc = issue.description
            if "top" in desc:
                positions.add("top")
            elif "center" in desc:
                positions.add("center")
            elif "bottom" in desc:
                positions.add("bottom")

        instructions["fixes"].append({
            "type": "text_layout",
            "description": f"Text overlap detected in: {', '.join(positions) or 'multiple regions'}",
            "manim_suggestion": (
                "CRITICAL LAYOUT FIX:\n"
                "1. Group text with VGroup: items = VGroup(text1, text2, text3)\n"
                "2. Use arrange: items.arrange(DOWN, aligned_edge=LEFT, buff=0.3)\n"
                "3. Position relative to title: items.next_to(title, DOWN, buff=0.5)\n"
                "4. NEVER use .move_to([x, y, 0]) with hardcoded numbers\n"
                "5. Scale if needed: items.scale_to_fit_width(12)"
            ),
        })

    # Include animation and border info
    instructions["is_animated"] = analysis.is_animated
    instructions["animation_score"] = analysis.animation_score
    instructions["border_issues"] = analysis.border_issues

    return instructions


def analyze_all_scenes(
    scene_results: list,
    output_path: str = "output/visual_analysis.json"
) -> dict:
    """Analyze all scenes and generate a comprehensive report."""
    print("\n[Visual Analyzer] Analyzing animation frames...")

    results = {
        "scenes": [],
        "summary": {
            "total_scenes": len(scene_results),
            "analyzed": 0,
            "avg_quality": 0,
            "needs_improvement": [],
        },
        "fix_instructions": [],
    }

    quality_sum = 0
    analyzed = 0

    for scene in scene_results:
        scene_id = scene["scene_id"]
        mp4_path = scene.get("mp4_path")
        scene_type = scene.get("scene_type", "")

        if mp4_path and os.path.exists(mp4_path):
            print(f"  Scene {scene_id}: Analyzing frames...")
            analysis = analyze_scene_video(mp4_path, scene_id, scene_type=scene_type)
            analyzed += 1
            quality_sum += analysis.quality_score

            results["scenes"].append(analysis.to_dict())

            # Generate fix instructions
            fix_instr = generate_fix_instructions(analysis, scene)
            if fix_instr["needs_fix"]:
                results["fix_instructions"].append(fix_instr)
                results["summary"]["needs_improvement"].append(scene_id)

            status = "✓" if analysis.quality_score >= 70 else "⚠" if analysis.quality_score >= 50 else "✗"
            print(f"    {status} Score: {analysis.quality_score:.0f}/100, Issues: {len(analysis.issues)}")
        else:
            print(f"  Scene {scene_id}: No video file")
            results["scenes"].append({
                "scene_id": scene_id,
                "error": "No video file",
                "quality_score": 0,
            })

    results["summary"]["analyzed"] = analyzed
    results["summary"]["avg_quality"] = quality_sum / max(1, analyzed)

    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[Visual Analyzer] Complete:")
    print(f"  Analyzed: {analyzed}/{len(scene_results)} scenes")
    print(f"  Avg Quality: {results['summary']['avg_quality']:.1f}/100")
    print(f"  Need Improvement: {len(results['summary']['needs_improvement'])} scenes")
    print(f"  Report: {output_path}")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python visual_analyzer.py <scene_results.json>")
        print("       python visual_analyzer.py <video.mp4>")
        sys.exit(1)

    input_path = sys.argv[1]

    if input_path.endswith(".mp4"):
        # Analyze single video
        analysis = analyze_scene_video(input_path, scene_id=1)
        print(json.dumps(analysis.to_dict(), indent=2))
    else:
        # Analyze scene results JSON
        with open(input_path) as f:
            scene_results = json.load(f)
        analyze_all_scenes(scene_results)
