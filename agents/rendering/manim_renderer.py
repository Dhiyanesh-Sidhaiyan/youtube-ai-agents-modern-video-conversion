"""
Manim rendering utilities — single source of truth for subprocess rendering.

Extracted from animation_agent.py to break the circular import:
  animation_agent ← dynamic_scene_generator → animation_agent.render_manim
  animation_agent ← animation_fixer         → animation_agent.render_manim

All files that need to render Manim code import from here.
"""

import os
import subprocess
import sys


def render_manim(scene_file: str, class_name: str, output_dir: str) -> tuple[bool, str]:
    """
    Attempt to render a Manim scene via subprocess.

    Args:
        scene_file: Path to the .py file containing the Manim scene class.
        class_name: Name of the Scene subclass to render (e.g. "Scene1").
        output_dir: Directory where Manim places media output.

    Returns:
        (success, error_message) — error_message is empty string on success.
    """
    cmd = [
        sys.executable, "-m", "manim",
        "-ql",  # low quality for speed during testing
        "--output_file", class_name,
        "--media_dir", output_dir,
        scene_file,
        class_name,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        return True, ""
    return False, result.stderr[-2000:]  # last 2000 chars of error


def find_rendered_mp4(class_name: str, search_root: str) -> str | None:
    """
    Walk search_root to find a rendered MP4 matching class_name.

    Args:
        class_name: Manim class name (e.g. "Scene1") — will look for "Scene1.mp4".
        search_root: Root directory to search recursively.

    Returns:
        Absolute path to the MP4, or None if not found.
    """
    for root, _, files in os.walk(search_root):
        for fname in files:
            if fname == f"{class_name}.mp4":
                return os.path.join(root, fname)
    return None
