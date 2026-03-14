"""
Self-Refine loop for scene generation.

Responsibility: Orchestrate the Generate → Evaluate → Feedback → Refine cycle.
This is the only file allowed to call both generate_fn and evaluate_scene_quality.
"""

from typing import Callable, Optional

from .scene_quality import PerSceneEvaluation, evaluate_scene_quality
from core.config import QUALITY_THRESHOLD, MAX_REFINE_ITERATIONS


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

    animation_feedback = ""
    if not eval_result.is_animated:
        animation_feedback = (
            f"\nANIMATION WARNING: Scene appears STATIC "
            f"(animation_score: {eval_result.animation_score:.0f}/100)\n"
            "- Add more self.play() calls with Write(), FadeIn(), Transform(), GrowFromCenter()"
        )

    border_feedback = ""
    if eval_result.border_issues:
        edges = ", ".join(eval_result.border_issues)
        border_feedback = (
            f"\nBORDER WARNING: Content may be cut off at: {edges}\n"
            "- Use .scale(0.8) on large elements\n"
            "- Avoid positions > 5 units from center"
        )

    return f"""
PREVIOUS ATTEMPT FEEDBACK (Iteration {iteration}):
Score: {eval_result.overall_score:.0f}/100 (need {QUALITY_THRESHOLD:.0f}+)
Visual Score: {eval_result.visual_score:.0f}/100
Technical Score: {eval_result.technical_score:.0f}/100
Animation Score: {eval_result.animation_score:.0f}/100
{animation_feedback}{border_feedback}

Issues detected:
{issues_str or "- No specific issues detected, but score is below threshold"}

Manim code suggestions:
{suggestions_str or "- Ensure animations are visible and well-positioned"}

IMPORTANT: Address ALL issues above in the new generation.
- Add a dark background rectangle if scene is too dark
- Use self.wait() to hold the final frame
- Scale down elements if they appear cut off
- Use brighter colors (WHITE, YELLOW, BLUE) for text
- Add more animations (Write, FadeIn, GrowFromCenter) if scene is static
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
        generate_fn: Function (scene, scenes_dir, feedback) -> mp4_path
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
        feedback_str = "\n".join(feedback_history) if feedback_history else None
        mp4_path = generate_fn(scene, scenes_dir, feedback=feedback_str)

        if not mp4_path:
            print(f"    Iteration {iteration}: Render FAILED")
            feedback_history.append(
                "CRITICAL: Previous render failed completely. "
                "Use simpler animations and verified Manim API calls."
            )
            continue

        eval_result = evaluate_scene_quality(scene, mp4_path, audio_path)
        eval_result.iteration = iteration
        score = eval_result.overall_score

        print(f"    Iteration {iteration}: Score {score:.0f}/100 "
              f"(visual: {eval_result.visual_score:.0f}, tech: {eval_result.technical_score:.0f})")

        if score > best_score:
            best_score = score
            best_mp4 = mp4_path
            best_eval = eval_result

        if score >= threshold:
            eval_result.passed_threshold = True
            print(f"    ✓ Scene {scene_id} PASSED ({score:.0f}/{threshold:.0f})")
            return mp4_path, eval_result

        feedback = generate_feedback_prompt(scene, eval_result, iteration)
        feedback_history.append(feedback)

        if eval_result.issues:
            print(f"    Issues: {', '.join(eval_result.issues[:3])}")

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
