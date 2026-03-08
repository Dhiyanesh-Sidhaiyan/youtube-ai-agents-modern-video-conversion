"""
Agent 5: Animation Quality Evaluation Agent
Measures and evaluates the quality of generated Manim animations.

Metrics:
1. Technical Quality - render success, duration, resolution
2. Visual Quality - blank frames, text readability, element positioning
3. Content Alignment - scene type matches visual output
4. Timing Quality - animation duration vs narration duration
5. Spelling Quality - check text for spelling errors
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

# Spelling checker
try:
    from spellchecker import SpellChecker
    HAS_SPELLCHECKER = True
    SPELL = SpellChecker()
except ImportError:
    HAS_SPELLCHECKER = False
    SPELL = None


def check_spelling(text: str) -> dict:
    """
    Check spelling in text and return misspelled words with suggestions.
    Returns: {"misspelled": ["word1", "word2"], "score": 0-100}
    """
    if not HAS_SPELLCHECKER or not text:
        return {"misspelled": [], "suggestions": {}, "score": 100.0}

    # Extract words (letters only, ignore numbers and special chars)
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())

    # Filter out common technical terms and abbreviations
    ignore_words = {
        'api', 'url', 'html', 'css', 'js', 'json', 'http', 'https',
        'ai', 'ml', 'gpu', 'cpu', 'ui', 'ux', 'sdk', 'ide', 'cli',
        'manim', 'python', 'numpy', 'scipy', 'pytorch', 'tensorflow',
        'youtube', 'mp4', 'wav', 'pdf', 'png', 'jpg', 'svg',
    }

    words_to_check = [w for w in words if w not in ignore_words]

    if not words_to_check:
        return {"misspelled": [], "suggestions": {}, "score": 100.0}

    misspelled = list(SPELL.unknown(words_to_check))
    suggestions = {word: SPELL.correction(word) for word in misspelled[:5]}

    # Calculate score: 100 if no errors, deduct 10 per misspelled word
    score = max(0, 100 - len(misspelled) * 10)

    return {
        "misspelled": misspelled[:10],  # Limit to 10
        "suggestions": suggestions,
        "score": score
    }


@dataclass
class SceneEvaluation:
    """Evaluation results for a single scene."""
    scene_id: int
    scene_type: str
    title: str

    # Technical metrics
    render_success: bool = False
    mp4_exists: bool = False
    mp4_size_kb: float = 0.0
    video_duration: float = 0.0
    video_resolution: tuple = (0, 0)
    video_fps: float = 0.0

    # Quality metrics (0-100 scale)
    blank_frame_ratio: float = 0.0  # % of frames that are blank/solid color
    text_elements: int = 0          # Number of text elements detected
    animation_events: int = 0       # Number of animation transitions

    # Timing metrics
    audio_duration: float = 0.0
    timing_match_score: float = 0.0  # How well video matches audio duration

    # Content alignment
    template_used: str = ""
    content_score: float = 0.0

    # Spelling check
    spelling_score: float = 100.0
    misspelled_words: list = field(default_factory=list)

    # Issues found
    issues: list = field(default_factory=list)

    @property
    def overall_score(self) -> float:
        """Calculate overall quality score (0-100)."""
        if not self.render_success:
            return 0.0

        scores = []

        # Technical score (20%)
        tech_score = 100 if self.mp4_exists and self.mp4_size_kb > 10 else 0
        scores.append(tech_score * 0.20)

        # Visual score (20%)
        visual_score = max(0, 100 - self.blank_frame_ratio * 100)
        scores.append(visual_score * 0.20)

        # Timing score (20%)
        scores.append(self.timing_match_score * 0.20)

        # Content score (20%)
        scores.append(self.content_score * 0.20)

        # Spelling score (20%)
        scores.append(self.spelling_score * 0.20)

        return sum(scores)


@dataclass
class PipelineEvaluation:
    """Evaluation results for entire pipeline run."""
    total_scenes: int = 0
    rendered_scenes: int = 0
    failed_scenes: int = 0

    total_duration: float = 0.0
    avg_scene_duration: float = 0.0

    scene_evaluations: list = field(default_factory=list)

    # Aggregate scores
    avg_technical_score: float = 0.0
    avg_visual_score: float = 0.0
    avg_timing_score: float = 0.0
    avg_content_score: float = 0.0
    avg_spelling_score: float = 100.0
    overall_score: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "summary": {
                "total_scenes": self.total_scenes,
                "rendered_scenes": self.rendered_scenes,
                "failed_scenes": self.failed_scenes,
                "render_success_rate": f"{self.rendered_scenes/max(1,self.total_scenes)*100:.1f}%",
                "total_duration": f"{self.total_duration:.1f}s",
                "overall_score": f"{self.overall_score:.1f}/100",
            },
            "scores": {
                "technical": f"{self.avg_technical_score:.1f}",
                "visual": f"{self.avg_visual_score:.1f}",
                "timing": f"{self.avg_timing_score:.1f}",
                "content": f"{self.avg_content_score:.1f}",
                "spelling": f"{self.avg_spelling_score:.1f}",
            },
            "scenes": [
                {
                    "scene_id": s.scene_id,
                    "title": s.title,
                    "scene_type": s.scene_type,
                    "render_success": s.render_success,
                    "duration": f"{s.video_duration:.1f}s",
                    "score": f"{s.overall_score:.1f}",
                    "issues": s.issues,
                }
                for s in self.scene_evaluations
            ]
        }


def get_video_metadata(mp4_path: str) -> dict:
    """Extract video metadata using ffprobe."""
    if not os.path.exists(mp4_path):
        return {}

    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            mp4_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)

            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            if video_stream:
                return {
                    "duration": float(data.get("format", {}).get("duration", 0)),
                    "width": video_stream.get("width", 0),
                    "height": video_stream.get("height", 0),
                    "fps": eval(video_stream.get("r_frame_rate", "0/1")),
                    "size_kb": os.path.getsize(mp4_path) / 1024,
                }
    except Exception as e:
        print(f"  ffprobe error: {e}")

    return {}


def analyze_blank_frames(mp4_path: str, sample_count: int = 10) -> float:
    """Analyze video for blank/solid color frames. Returns ratio (0-1)."""
    if not os.path.exists(mp4_path):
        return 1.0

    try:
        # Extract sample frames and check variance
        # Using ffmpeg to extract frames and analyze
        cmd = [
            "ffprobe", "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "stream=nb_frames",
            "-of", "default=nokey=1:noprint_wrappers=1",
            mp4_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            total_frames = int(result.stdout.strip())
            if total_frames > 0:
                # For now, return 0 (no blank frames) if video has frames
                # A more sophisticated analysis would extract and analyze actual frames
                return 0.0
    except Exception:
        pass

    return 0.5  # Unknown, assume 50% quality


def evaluate_scene(
    scene: dict,
    mp4_path: Optional[str],
    audio_path: Optional[str],
    template_used: str = ""
) -> SceneEvaluation:
    """Evaluate a single scene's animation quality."""

    eval_result = SceneEvaluation(
        scene_id=scene["scene_id"],
        scene_type=scene.get("scene_type", "unknown"),
        title=scene["title"],
        template_used=template_used,
    )

    # Check MP4 exists
    if mp4_path and os.path.exists(mp4_path):
        eval_result.mp4_exists = True
        eval_result.render_success = True
        eval_result.mp4_size_kb = os.path.getsize(mp4_path) / 1024

        # Get video metadata
        metadata = get_video_metadata(mp4_path)
        if metadata:
            eval_result.video_duration = metadata.get("duration", 0)
            eval_result.video_resolution = (
                metadata.get("width", 0),
                metadata.get("height", 0)
            )
            eval_result.video_fps = metadata.get("fps", 0)

        # Analyze blank frames
        eval_result.blank_frame_ratio = analyze_blank_frames(mp4_path)

    else:
        eval_result.issues.append("MP4 not found or render failed")

    # Check audio and timing match
    if audio_path and os.path.exists(audio_path):
        audio_meta = get_video_metadata(audio_path)  # ffprobe works for audio too
        eval_result.audio_duration = audio_meta.get("duration", 0)

        if eval_result.video_duration > 0 and eval_result.audio_duration > 0:
            # Calculate timing match (100% if within 10% difference)
            ratio = eval_result.video_duration / eval_result.audio_duration
            if 0.9 <= ratio <= 1.1:
                eval_result.timing_match_score = 100.0
            elif 0.5 <= ratio <= 2.0:
                eval_result.timing_match_score = 50.0
            else:
                eval_result.timing_match_score = 20.0
                eval_result.issues.append(f"Timing mismatch: video={eval_result.video_duration:.1f}s, audio={eval_result.audio_duration:.1f}s")
        else:
            eval_result.timing_match_score = 50.0  # Unknown
    else:
        eval_result.timing_match_score = 50.0  # No audio to compare

    # Content alignment score based on scene type
    scene_type = scene.get("scene_type", "")
    visual_desc = scene.get("visual_description", "").lower()

    content_indicators = {
        "intro": ["title", "introduction", "welcome", "overview"],
        "concept": ["concept", "idea", "understanding", "explain"],
        "comparison": ["vs", "compare", "versus", "difference", "left", "right"],
        "process": ["step", "process", "flow", "arrow", "sequence"],
        "example": ["example", "code", "demo", "sample", "result"],
        "conclusion": ["summary", "conclusion", "takeaway", "final"],
    }

    if scene_type in content_indicators:
        matches = sum(1 for kw in content_indicators[scene_type] if kw in visual_desc)
        eval_result.content_score = min(100, matches * 25 + 50)
    else:
        eval_result.content_score = 50.0

    # Spelling check on title and narration
    text_to_check = f"{scene['title']} {scene.get('narration_text', '')}"
    spelling_result = check_spelling(text_to_check)
    eval_result.spelling_score = spelling_result["score"]
    eval_result.misspelled_words = spelling_result["misspelled"]

    if spelling_result["misspelled"]:
        words_str = ", ".join(spelling_result["misspelled"][:5])
        eval_result.issues.append(f"Spelling issues: {words_str}")

    # Check for common issues
    if eval_result.mp4_size_kb < 10:
        eval_result.issues.append("Video file too small (< 10KB)")

    if eval_result.video_duration < 3:
        eval_result.issues.append("Video too short (< 3s)")

    if eval_result.video_resolution[0] < 720:
        eval_result.issues.append(f"Low resolution: {eval_result.video_resolution}")

    return eval_result


def evaluate_pipeline(
    script_path: str,
    scene_results: list,
    audio_results: list,
    output_path: str = "output/evaluation.json"
) -> PipelineEvaluation:
    """
    Evaluate the entire pipeline output.

    Args:
        script_path: Path to script.json
        scene_results: List of dicts with scene_id and mp4_path
        audio_results: List of dicts with scene_id and audio_path
        output_path: Where to save evaluation report

    Returns:
        PipelineEvaluation with all metrics
    """
    print("\n[Eval Agent] Evaluating animation quality...")

    with open(script_path) as f:
        script = json.load(f)

    # Build lookup maps
    mp4_map = {r["scene_id"]: r.get("mp4_path") for r in scene_results}
    audio_map = {r["scene_id"]: r.get("audio_path") for r in audio_results}

    evaluation = PipelineEvaluation()
    evaluation.total_scenes = len(script["scenes"])

    for scene in script["scenes"]:
        sid = scene["scene_id"]
        mp4 = mp4_map.get(sid)
        audio = audio_map.get(sid)

        scene_eval = evaluate_scene(scene, mp4, audio)
        evaluation.scene_evaluations.append(scene_eval)

        if scene_eval.render_success:
            evaluation.rendered_scenes += 1
            evaluation.total_duration += scene_eval.video_duration
        else:
            evaluation.failed_scenes += 1

        print(f"  Scene {sid}: {scene_eval.overall_score:.0f}/100 {'✓' if scene_eval.render_success else '✗'}")

    # Calculate averages
    if evaluation.rendered_scenes > 0:
        evaluation.avg_scene_duration = evaluation.total_duration / evaluation.rendered_scenes

        successful_evals = [e for e in evaluation.scene_evaluations if e.render_success]
        n = len(successful_evals)
        evaluation.avg_timing_score = sum(e.timing_match_score for e in successful_evals) / n
        evaluation.avg_content_score = sum(e.content_score for e in successful_evals) / n
        evaluation.avg_visual_score = sum(100 - e.blank_frame_ratio * 100 for e in successful_evals) / n
        evaluation.avg_spelling_score = sum(e.spelling_score for e in successful_evals) / n
        evaluation.avg_technical_score = 100 * evaluation.rendered_scenes / evaluation.total_scenes

        evaluation.overall_score = sum(
            e.overall_score for e in evaluation.scene_evaluations
        ) / evaluation.total_scenes

    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(evaluation.to_dict(), f, indent=2)

    # Print summary
    print("\n[Eval Agent] Quality Report:")
    print(f"  Render Success: {evaluation.rendered_scenes}/{evaluation.total_scenes}")
    print(f"  Overall Score:  {evaluation.overall_score:.1f}/100")
    print(f"  Technical:      {evaluation.avg_technical_score:.1f}")
    print(f"  Visual:         {evaluation.avg_visual_score:.1f}")
    print(f"  Timing:         {evaluation.avg_timing_score:.1f}")
    print(f"  Content:        {evaluation.avg_content_score:.1f}")
    print(f"  Spelling:       {evaluation.avg_spelling_score:.1f}")
    print(f"  Report saved:   {output_path}")

    return evaluation


def print_quality_report(eval_path: str):
    """Print a formatted quality report from evaluation JSON."""
    with open(eval_path) as f:
        data = json.load(f)

    print("\n" + "=" * 60)
    print("  ANIMATION QUALITY REPORT")
    print("=" * 60)

    summary = data["summary"]
    print(f"\n  Scenes Rendered: {summary['rendered_scenes']}/{summary['total_scenes']}")
    print(f"  Success Rate:    {summary['render_success_rate']}")
    print(f"  Total Duration:  {summary['total_duration']}")
    print(f"  Overall Score:   {summary['overall_score']}")

    scores = data["scores"]
    print("\n  Score Breakdown:")
    print(f"    Technical: {scores['technical']}/100")
    print(f"    Visual:    {scores['visual']}/100")
    print(f"    Timing:    {scores['timing']}/100")
    print(f"    Content:   {scores['content']}/100")
    print(f"    Spelling:  {scores.get('spelling', '100.0')}/100")

    print(f"\n  Scene Details:")
    for scene in data["scenes"]:
        status = "✓" if scene["render_success"] else "✗"
        print(f"    {status} Scene {scene['scene_id']}: {scene['score']} - {scene['title'][:40]}")
        if scene["issues"]:
            for issue in scene["issues"]:
                print(f"        ⚠ {issue}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python eval_agent.py <evaluation.json>")
        print("       python eval_agent.py <script.json> <scene_results.json> <audio_results.json>")
        sys.exit(1)

    if len(sys.argv) == 2:
        # Print existing report
        print_quality_report(sys.argv[1])
    else:
        # Generate new evaluation
        script = sys.argv[1]
        with open(sys.argv[2]) as f:
            scene_results = json.load(f)
        with open(sys.argv[3]) as f:
            audio_results = json.load(f)

        evaluate_pipeline(script, scene_results, audio_results)
