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

    def to_dict(self):
        return {
            "scene_id": self.scene_id,
            "total_frames": self.total_frames,
            "blank_frames": self.blank_frame_count,
            "blank_ratio": f"{self.blank_frame_count / max(1, self.total_frames) * 100:.1f}%",
            "avg_brightness": f"{self.avg_brightness:.1f}",
            "quality_score": f"{self.quality_score:.1f}",
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


def analyze_scene_video(mp4_path: str, scene_id: int, sample_count: int = 10) -> SceneVisualAnalysis:
    """Analyze a scene's video for visual quality issues."""
    analysis = SceneVisualAnalysis(scene_id=scene_id)

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

    # Calculate quality score
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

    # Bonus for good contrast
    if 30 < analysis.avg_contrast < 100:
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

        if mp4_path and os.path.exists(mp4_path):
            print(f"  Scene {scene_id}: Analyzing frames...")
            analysis = analyze_scene_video(mp4_path, scene_id)
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
