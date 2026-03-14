"""
Per-scene quality evaluation combining visual and technical metrics.

Responsibility: Evaluate a single rendered scene against quality thresholds.
No orchestration, no self-refine loop — just measurement and scoring.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from agents.visual_analysis import (
    analyze_scene_video,
    generate_fix_instructions,
    SceneVisualAnalysis,
)
from agents.eval_agent import evaluate_scene, SceneEvaluation
from core.config import (
    QUALITY_THRESHOLD,
    VISUAL_WEIGHT,
    TECHNICAL_WEIGHT,
)


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
    result.fix_instructions = _enhance_fix_instructions(result.fix_instructions, result.issues)

    return result


def _enhance_fix_instructions(fix_instructions: dict, issues: list) -> dict:
    """Enhance fix instructions with more specific Manim guidance."""
    enhanced = fix_instructions.copy()
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
