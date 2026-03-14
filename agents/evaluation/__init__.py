"""
agents.evaluation — Scene quality evaluation and self-refine orchestration.

Responsibility split:
    scene_quality.py    — Per-scene visual + technical evaluation
    self_refine.py      — Generate → Evaluate → Feedback → Refine loop
    content_variety.py  — Script-level variety checking (not per-scene)

Public API (backward compatible with agents.scene_evaluator):
    PerSceneEvaluation
    evaluate_scene_quality(scene, mp4_path, audio_path) -> PerSceneEvaluation
    generate_with_self_refine(scene, scenes_dir, generate_fn, ...) -> (mp4_path, eval)
    evaluate_all_scenes_summary(evaluations) -> dict
    check_content_variety(scenes) -> dict
    validate_script_variety(script) -> dict
"""

from .scene_quality import PerSceneEvaluation, evaluate_scene_quality
from .self_refine import (
    generate_with_self_refine,
    generate_feedback_prompt,
    evaluate_all_scenes_summary,
)
from .content_variety import (
    check_content_variety,
    extract_visual_patterns,
    validate_script_variety,
)

__all__ = [
    "PerSceneEvaluation",
    "evaluate_scene_quality",
    "generate_with_self_refine",
    "generate_feedback_prompt",
    "evaluate_all_scenes_summary",
    "check_content_variety",
    "extract_visual_patterns",
    "validate_script_variety",
]
