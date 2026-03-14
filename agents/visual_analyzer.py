"""
DEPRECATED: agents.visual_analyzer has been split into agents.visual_analysis package.
This file is kept as a backward-compatibility shim.

Use instead:
    from agents.visual_analysis import analyze_scene_video, generate_fix_instructions
"""
import warnings
warnings.warn(
    "agents.visual_analyzer is deprecated. Use agents.visual_analysis instead.",
    DeprecationWarning,
    stacklevel=2,
)

from agents.visual_analysis import (  # noqa: F401
    VisualIssue,
    FrameAnalysis,
    SceneVisualAnalysis,
    analyze_scene_video,
    generate_fix_instructions,
    analyze_all_scenes,
)

__all__ = [
    "VisualIssue",
    "FrameAnalysis",
    "SceneVisualAnalysis",
    "analyze_scene_video",
    "generate_fix_instructions",
    "analyze_all_scenes",
]
