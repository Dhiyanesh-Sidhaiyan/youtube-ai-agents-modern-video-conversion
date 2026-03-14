"""
agents.visual_analysis — Frame-by-frame visual quality analysis.

Public API (backward compatible with agents.visual_analyzer):
    VisualIssue
    FrameAnalysis
    SceneVisualAnalysis
    analyze_scene_video(mp4_path, scene_id, sample_count) -> SceneVisualAnalysis
    generate_fix_instructions(visual, scene) -> dict
    analyze_all_scenes(scene_results, scenes_dir, output_path) -> dict
"""
from .frame_analyzer import (
    VisualIssue,
    FrameAnalysis,
    SceneVisualAnalysis,
    analyze_scene_video,
)
from .fix_generator import (
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
