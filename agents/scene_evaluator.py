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
    # New fields for detailed evaluation
    is_animated: bool = True
    animation_score: float = 100.0
    border_issues: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "overall_score": self.overall_score,
            "visual_score": self.visual_score,
            "technical_score": self.technical_score,
            "is_animated": self.is_animated,
            "animation_score": self.animation_score,
            "border_issues": self.border_issues,
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

    # Visual analysis (brightness, contrast, blank frames, offscreen content, animation, borders)
    visual: SceneVisualAnalysis = analyze_scene_video(mp4_path, scene_id, sample_count=10)
    result.visual_score = visual.quality_score

    # Capture new animation and border analysis
    result.is_animated = visual.is_animated
    result.animation_score = visual.animation_score
    result.border_issues = visual.border_issues

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

    if "offscreen" in issue_text or "cut off" in issue_text or "border" in issue_text:
        enhanced.setdefault("fixes", []).append({
            "type": "positioning",
            "description": "Content may be cut off at edges",
            "manim_suggestion": (
                "Scale down: .scale(0.8); "
                "Use .to_edge() with buff=0.5; "
                "Check element positions with .get_center()"
            ),
        })

    if "static" in issue_text or "minimal animation" in issue_text:
        enhanced.setdefault("fixes", []).append({
            "type": "animation",
            "description": "Scene appears static - add more animations",
            "manim_suggestion": (
                "Add animations for each element: self.play(Write(text)); "
                "Use LaggedStart(*[FadeIn(item) for item in items]); "
                "Add GrowFromCenter() for shapes"
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

    # Build animation feedback
    animation_feedback = ""
    if not eval_result.is_animated:
        animation_feedback = f"\nANIMATION WARNING: Scene appears STATIC (animation_score: {eval_result.animation_score:.0f}/100)\n- Add more self.play() calls with Write(), FadeIn(), Transform(), GrowFromCenter()"

    # Build border feedback
    border_feedback = ""
    if eval_result.border_issues:
        edges = ", ".join(eval_result.border_issues)
        border_feedback = f"\nBORDER WARNING: Content may be cut off at: {edges}\n- Use .scale(0.8) on large elements\n- Avoid positions > 5 units from center"

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


# ─── Content Variety Scoring (NotebookLM Quality) ────────────────────────────

import re
from collections import Counter


def check_content_variety(scenes: list) -> dict:
    """
    Detect and penalize repetitive patterns in scene content.
    This ensures NotebookLM-quality variety in generated scripts.

    Args:
        scenes: List of scene dicts from script.json

    Returns:
        {
            "variety_score": int (0-100),
            "issues": list of issue descriptions,
            "scene_type_distribution": dict,
            "recommendations": list of suggestions
        }
    """
    issues = []
    recommendations = []
    score = 100

    if not scenes:
        return {"variety_score": 0, "issues": ["No scenes to evaluate"], "recommendations": []}

    # 1. Check scene type distribution - penalize overuse
    scene_types = [s.get("scene_type", "unknown") for s in scenes]
    type_counts = Counter(scene_types)
    scene_count = len(scenes)

    for scene_type, count in type_counts.items():
        usage_ratio = count / scene_count
        if usage_ratio > 0.4:
            issues.append(f"Scene type '{scene_type}' overused: {count}/{scene_count} ({usage_ratio*100:.0f}%)")
            score -= 15
            recommendations.append(f"Replace some '{scene_type}' scenes with: comparison, data_chart, timeline, diagram")

    # 2. Check for generic step patterns
    generic_patterns = [
        r"Step 1[^a-z]", r"Step 2[^a-z]", r"Step 3[^a-z]",
        r"Point 1[^a-z]", r"Point 2[^a-z]", r"Point 3[^a-z]",
        r"Feature A[^a-z]", r"Feature B[^a-z]",
        r"Item 1[^a-z]", r"Item 2[^a-z]",
    ]

    for scene in scenes:
        visual_desc = scene.get("visual_description", "")
        narration = scene.get("narration_text", "")
        combined = f"{visual_desc} {narration}"

        for pattern in generic_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                issues.append(f"Scene {scene.get('scene_id', '?')}: Contains generic '{pattern.replace('[^a-z]', '')}' pattern")
                score -= 20
                recommendations.append(f"Scene {scene.get('scene_id')}: Replace generic steps with specific content from transcript")
                break  # Only penalize once per scene

    # 3. Check for visual variety - detect repeated layouts
    visual_patterns = extract_visual_patterns(scenes)
    pattern_counts = Counter(visual_patterns)

    repeated = [(p, c) for p, c in pattern_counts.items() if c > 2 and p != "unknown"]
    for pattern, count in repeated:
        issues.append(f"Visual pattern '{pattern}' repeated {count} times")
        score -= 10
        recommendations.append(f"Vary '{pattern}' layout: try side-by-side, radial, or timeline instead")

    # 4. Check narration variety - similar sentence structures
    narrations = [s.get("narration_text", "")[:50] for s in scenes]
    similar_starts = Counter([n.split()[0] if n else "" for n in narrations])

    for start, count in similar_starts.items():
        if count > 2 and start and len(start) > 2:
            issues.append(f"Narration often starts with '{start}' ({count} times)")
            score -= 5
            recommendations.append("Vary narration openings: use questions, surprising facts, 'What if...'")

    # 5. Check for analogy presence (NotebookLM quality marker)
    analogy_keywords = ["like", "imagine", "think of", "similar to", "just like", "as if"]
    analogy_count = 0
    for scene in scenes:
        text = f"{scene.get('narration_text', '')} {scene.get('visual_description', '')}".lower()
        if any(kw in text for kw in analogy_keywords):
            analogy_count += 1

    expected_analogies = max(1, len(scenes) // 2)  # At least 1 per 2 scenes
    if analogy_count < expected_analogies:
        issues.append(f"Low analogy count: {analogy_count} (expected {expected_analogies}+)")
        score -= 10
        recommendations.append("Add analogies: 'Think of X like Y...' for abstract concepts")

    # Ensure score stays in valid range
    score = max(0, min(100, score))

    return {
        "variety_score": score,
        "issues": issues,
        "scene_type_distribution": dict(type_counts),
        "analogy_count": analogy_count,
        "recommendations": recommendations
    }


def extract_visual_patterns(scenes: list) -> list:
    """
    Extract visual layout patterns from scene descriptions.
    Used to detect repetitive visual approaches.
    """
    patterns = []

    layout_keywords = {
        "side-by-side": ["side by side", "side-by-side", "left and right", "two columns"],
        "flow-diagram": ["flow", "arrows between", "connected steps", "→"],
        "centered-text": ["centered", "center of screen", "middle"],
        "bullet-list": ["bullet", "list of", "points"],
        "comparison-boxes": ["two boxes", "comparison", "vs", "versus"],
        "timeline": ["timeline", "sequence", "chronological"],
        "radial": ["radial", "circular", "around center"],
        "hierarchy": ["hierarchy", "tree", "parent-child"],
        "chart": ["chart", "graph", "bar", "pie", "data"],
    }

    for scene in scenes:
        visual_desc = scene.get("visual_description", "").lower()
        pattern_found = "unknown"

        for pattern_name, keywords in layout_keywords.items():
            if any(kw in visual_desc for kw in keywords):
                pattern_found = pattern_name
                break

        patterns.append(pattern_found)

    return patterns


def validate_script_variety(script: dict) -> dict:
    """
    Validate a complete script for content variety.
    Returns variety check results plus recommendations.

    Args:
        script: Script dict with "scenes" key

    Returns:
        Variety check results with pass/fail status
    """
    scenes = script.get("scenes", [])
    result = check_content_variety(scenes)

    # Determine if script passes variety requirements
    passed = result["variety_score"] >= 70 and len(result["issues"]) <= 3

    result["passed"] = passed
    result["status"] = "PASSED" if passed else "NEEDS_IMPROVEMENT"

    if not passed:
        print(f"\n[Variety Check] Score: {result['variety_score']}/100 - NEEDS IMPROVEMENT")
        for issue in result["issues"][:5]:
            print(f"  ⚠️  {issue}")
        print("\nRecommendations:")
        for rec in result["recommendations"][:3]:
            print(f"  → {rec}")
    else:
        print(f"\n[Variety Check] Score: {result['variety_score']}/100 - PASSED ✓")

    return result


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
