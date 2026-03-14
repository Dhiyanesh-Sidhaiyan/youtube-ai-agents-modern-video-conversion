"""
DEPRECATED: agents.scene_evaluator has been split into agents.evaluation package.
This file is kept as a backward-compatibility shim.

Use instead:
    from agents.evaluation import (
        PerSceneEvaluation,
        evaluate_scene_quality,
        generate_with_self_refine,
        evaluate_all_scenes_summary,
    )
"""
import warnings
warnings.warn(
    "agents.scene_evaluator is deprecated. Use agents.evaluation instead.",
    DeprecationWarning,
    stacklevel=2,
)

from agents.evaluation import (  # noqa: F401
    PerSceneEvaluation,
    evaluate_scene_quality,
    generate_with_self_refine,
    generate_feedback_prompt,
    evaluate_all_scenes_summary,
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
