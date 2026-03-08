"""
Per-Scene Evaluator with Self-Refine Loop

Implements the Generate → Evaluate → Feedback → Refine cycle for each scene.
This ensures each scene meets quality standards before moving to the next.

Based on research:
- Self-Refine: Iterative Refinement with Self-Feedback (arxiv.org/abs/2303.17651)
- Evaluator Reflect-Refine Loop Patterns (AWS Prescriptive Guidance)
"""

import os
from dataclasses import dataclass, field
from typing import Callable, Optional

from agents.visual_analyzer import (
    analyze_scene_video,
    generate_fix_instructions,
    SceneVisualAnalysis,
)
from agents.eval_agent import evaluate_scene, SceneEvaluation


QUALITY_THRESHOLD = 80.0
MAX_REFINE_ITERATIONS = 3

# Weight distribution for combined scoring
VISUAL_WEIGHT = 0.6
TECHNICAL_WEIGHT = 0.4


@dataclass
class PerSceneEvaluation:
    """Combined evaluation result for a single scene."""
    scene_id: int
    overall_score: float = 0.0
    visual_score: float = 0.0
    technical_score: float = 0.0
    issues: list = field(default_factory=list)
    fix_instructions: dict = field(default_factory=dict)
    iteration: int = 0
    passed_threshold: bool = False

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "overall_score": self.overall_score,
            "visual_score": self.visual_score,
            "technical_score": self.technical_score,
            "issues": self.issues,
            "iteration": self.iteration,
            "passed_threshold": self.passed_threshold,
        }


def evaluate_scene_quality(
    scene: dict,
    mp4_path: str,
    audio_path: Optional[str] = None
) -> PerSceneEvaluation:
    """
    Comprehensive single-scene evaluation combining visual and technical metrics.

    Args:
        scene: Scene dict with scene_id, title, narration_text, etc.
        mp4_path: Path to rendered MP4 video.
        audio_path: Optional path to audio file for timing analysis.

    Returns:
        PerSceneEvaluation with combined scores and fix instructions.
    """
    scene_id = scene["scene_id"]
    result = PerSceneEvaluation(scene_id=scene_id)

    if not mp4_path or not os.path.exists(mp4_path):
        result.issues.append("No MP4 file - render failed")
        result.fix_instructions = {
            "scene_id": scene_id,
            "needs_fix": True,
            "fixes": [{"type": "render_failure", "description": "Scene failed to render"}],
        }
        return result

    # Visual analysis (brightness, contrast, blank frames, offscreen content)
    visual: SceneVisualAnalysis = analyze_scene_video(mp4_path, scene_id, sample_count=10)
    result.visual_score = visual.quality_score

    # Technical evaluation (render success, duration, content alignment, spelling)
    technical: SceneEvaluation = evaluate_scene(scene, mp4_path, audio_path)
    result.technical_score = technical.overall_score

    # Combine scores with weights
    result.overall_score = (
        visual.quality_score * VISUAL_WEIGHT +
        technical.overall_score * TECHNICAL_WEIGHT
    )

    # Collect issues from both analyzers
    result.issues = [issue.description for issue in visual.issues]
    result.issues.extend(technical.issues)

    # Check if passes threshold
    result.passed_threshold = result.overall_score >= QUALITY_THRESHOLD

    # Generate fix instructions from visual analysis
    result.fix_instructions = generate_fix_instructions(visual, scene)

    # Add Manim-specific suggestions based on common issues
    result.fix_instructions = _enhance_fix_instructions(result.fix_instructions, result.issues)

    return result


def _enhance_fix_instructions(fix_instructions: dict, issues: list) -> dict:
    """Enhance fix instructions with more specific Manim guidance."""
    enhanced = fix_instructions.copy()

    # Look for specific patterns in issues
    issue_text = " ".join(issues).lower()

    if "dark" in issue_text or "brightness" in issue_text:
        enhanced.setdefault("fixes", []).append({
            "type": "colors",
            "description": "Scene too dark - add background or use brighter colors",
            "manim_suggestion": (
                "Add dark background rectangle: "
                "bg = Rectangle(width=16, height=10, fill_color='#1a1a2e', fill_opacity=1); "
                "self.add(bg)"
            ),
        })

    if "blank" in issue_text or "empty" in issue_text:
        enhanced.setdefault("fixes", []).append({
            "type": "animation_content",
            "description": "Blank frames detected - extend animations or add wait()",
            "manim_suggestion": (
                "Add self.wait(2) after animations; "
                "Remove FadeOut at end to preserve final frame"
            ),
        })

    if "offscreen" in issue_text or "cut off" in issue_text:
        enhanced.setdefault("fixes", []).append({
            "type": "positioning",
            "description": "Content may be cut off at edges",
            "manim_suggestion": (
                "Scale down: .scale(0.8); "
                "Use .to_edge() with buff=0.5; "
                "Check element positions with .get_center()"
            ),
        })

    return enhanced


def generate_feedback_prompt(
    scene: dict,
    eval_result: PerSceneEvaluation,
    iteration: int
) -> str:
    """
    Generate a feedback prompt for the LLM to improve the scene.

    Returns formatted feedback string to inject into the generation prompt.
    """
    issues_str = "\n".join(f"- {issue}" for issue in eval_result.issues[:5])

    manim_suggestions = []
    for fix in eval_result.fix_instructions.get("fixes", []):
        if "manim_suggestion" in fix:
            manim_suggestions.append(fix["manim_suggestion"])

    suggestions_str = "\n".join(f"- {s}" for s in manim_suggestions[:3])

    return f"""
PREVIOUS ATTEMPT FEEDBACK (Iteration {iteration}):
Score: {eval_result.overall_score:.0f}/100 (need {QUALITY_THRESHOLD:.0f}+)
Visual Score: {eval_result.visual_score:.0f}/100
Technical Score: {eval_result.technical_score:.0f}/100

Issues detected:
{issues_str or "- No specific issues detected, but score is below threshold"}

Manim code suggestions:
{suggestions_str or "- Ensure animations are visible and well-positioned"}

IMPORTANT: Address ALL issues above in the new generation.
- Add a dark background rectangle if scene is too dark
- Use self.wait() to hold the final frame
- Scale down elements if they appear cut off
- Use brighter colors (WHITE, YELLOW, BLUE) for text
"""


def generate_with_self_refine(
    scene: dict,
    scenes_dir: str,
    generate_fn: Callable,
    audio_path: Optional[str] = None,
    threshold: float = QUALITY_THRESHOLD,
    max_iter: int = MAX_REFINE_ITERATIONS,
) -> tuple[Optional[str], PerSceneEvaluation]:
    """
    Self-Refine loop for scene generation.

    Generates a scene, evaluates quality, and if below threshold,
    regenerates with feedback until threshold is met or max iterations reached.

    Args:
        scene: Scene dict from script.json
        scenes_dir: Directory to save scene files
        generate_fn: Function to call for generation: (scene, scenes_dir, feedback) -> mp4_path
        audio_path: Optional audio file for timing analysis
        threshold: Quality threshold (0-100) to pass
        max_iter: Maximum refinement iterations

    Returns:
        Tuple of (best_mp4_path, final_evaluation)
    """
    scene_id = scene["scene_id"]
    best_mp4 = None
    best_score = 0.0
    best_eval = PerSceneEvaluation(scene_id=scene_id)
    feedback_history: list[str] = []

    print(f"\n[Scene Evaluator] Starting self-refine for Scene {scene_id}")

    for iteration in range(1, max_iter + 1):
        # GENERATE: Create scene with accumulated feedback
        feedback_str = "\n".join(feedback_history) if feedback_history else None
        mp4_path = generate_fn(scene, scenes_dir, feedback=feedback_str)

        if not mp4_path:
            print(f"    Iteration {iteration}: Render FAILED")
            # Add render failure to feedback
            feedback_history.append(
                "CRITICAL: Previous render failed completely. "
                "Use simpler animations and verified Manim API calls."
            )
            continue

        # EVALUATE: Analyze the generated scene
        eval_result = evaluate_scene_quality(scene, mp4_path, audio_path)
        eval_result.iteration = iteration
        score = eval_result.overall_score

        print(f"    Iteration {iteration}: Score {score:.0f}/100 "
              f"(visual: {eval_result.visual_score:.0f}, tech: {eval_result.technical_score:.0f})")

        # Track best attempt
        if score > best_score:
            best_score = score
            best_mp4 = mp4_path
            best_eval = eval_result

        # SUCCESS: Meets threshold
        if score >= threshold:
            eval_result.passed_threshold = True
            print(f"    ✓ Scene {scene_id} PASSED ({score:.0f}/{threshold:.0f})")
            return mp4_path, eval_result

        # FEEDBACK: Generate improvement instructions for next iteration
        feedback = generate_feedback_prompt(scene, eval_result, iteration)
        feedback_history.append(feedback)

        # Log issues
        if eval_result.issues:
            print(f"    Issues: {', '.join(eval_result.issues[:3])}")

    # Return best attempt even if below threshold
    print(f"    ⚠ Scene {scene_id} best: {best_score:.0f}/{threshold:.0f} (after {max_iter} iterations)")
    best_eval.passed_threshold = False
    return best_mp4, best_eval


def evaluate_all_scenes_summary(evaluations: list[PerSceneEvaluation]) -> dict:
    """Generate a summary of all per-scene evaluations."""
    if not evaluations:
        return {"scenes": 0, "avg_score": 0, "passed": 0, "failed": 0}

    total = len(evaluations)
    passed = sum(1 for e in evaluations if e.passed_threshold)
    avg_score = sum(e.overall_score for e in evaluations) / total

    return {
        "total_scenes": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": f"{passed/total*100:.1f}%",
        "avg_score": f"{avg_score:.1f}/100",
        "avg_visual": f"{sum(e.visual_score for e in evaluations)/total:.1f}/100",
        "avg_technical": f"{sum(e.technical_score for e in evaluations)/total:.1f}/100",
        "details": [e.to_dict() for e in evaluations],
    }


if __name__ == "__main__":
    # Test mode: evaluate a single scene video
    import sys
    import json

    if len(sys.argv) < 3:
        print("Usage: python scene_evaluator.py <scene.json> <video.mp4>")
        print("  scene.json should contain: {scene_id, title, visual_description, ...}")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        scene = json.load(f)

    mp4_path = sys.argv[2]
    result = evaluate_scene_quality(scene, mp4_path)

    print(f"\n=== Scene {result.scene_id} Evaluation ===")
    print(f"Overall Score: {result.overall_score:.1f}/100")
    print(f"Visual Score:  {result.visual_score:.1f}/100")
    print(f"Technical:     {result.technical_score:.1f}/100")
    print(f"Threshold:     {QUALITY_THRESHOLD:.0f}")
    print(f"Passed:        {'Yes' if result.passed_threshold else 'No'}")
    print(f"\nIssues ({len(result.issues)}):")
    for issue in result.issues:
        print(f"  - {issue}")
    print(f"\nFixes ({len(result.fix_instructions.get('fixes', []))}):")
    for fix in result.fix_instructions.get("fixes", []):
        print(f"  [{fix['type']}] {fix['description']}")
