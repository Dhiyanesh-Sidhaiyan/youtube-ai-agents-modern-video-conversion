"""
agents.rendering — Manim subprocess rendering utilities.

Public API:
    render_manim(scene_file, class_name, output_dir) -> (bool, str)
    find_rendered_mp4(class_name, search_root) -> str | None
"""

from .manim_renderer import render_manim, find_rendered_mp4

__all__ = ["render_manim", "find_rendered_mp4"]
