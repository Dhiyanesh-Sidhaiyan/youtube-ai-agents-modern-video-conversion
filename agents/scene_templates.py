"""
DEPRECATED: agents.scene_templates is replaced by agents.templates package.
This file is kept as a backward-compatibility shim.
Use: from agents.templates import generate_scene_code, SCENE_TEMPLATES
"""
import warnings
warnings.warn(
    "agents.scene_templates is deprecated. Use agents.templates instead.",
    DeprecationWarning,
    stacklevel=2,
)
from agents.templates import generate_scene_code, SCENE_TEMPLATES  # noqa: F401

__all__ = ["generate_scene_code", "SCENE_TEMPLATES"]
