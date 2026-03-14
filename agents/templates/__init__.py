"""
agents.templates — Scene template system for Manim animations.

Public API (backward compatible with agents.scene_templates):
    generate_scene_code(scene: dict) -> str
    SCENE_TEMPLATES: dict[str, str]
"""
from .registry import generate_scene_code
from .template_strings import SCENE_TEMPLATES

__all__ = ["generate_scene_code", "SCENE_TEMPLATES"]
