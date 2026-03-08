"""
Agent 2: Animation Code Agent
Converts visual scene descriptions into Manim Community Edition Python code,
renders each scene to MP4. Uses a Writer+Reviewer retry loop for reliability.
Inspired by: github.com/makefinks/manim-generator
"""

import json
import os
import re
import subprocess
import sys
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
WRITER_MODEL = "phi4"
REVIEWER_MODEL = "llama3.2:3b"  # fast 3B model for review pass
MAX_RETRIES = 3
OLLAMA_TIMEOUT = 300  # seconds — phi4 14B needs time on CPU/low-VRAM

WRITER_PROMPT = """You are a Manim Community Edition expert. Write a complete, self-contained
Manim scene class for the following visual description.

Rules:
- Use ONLY Manim Community Edition (manim) imports
- Class name must be exactly: Scene{scene_id}
- Use simple shapes: Text, Circle, Rectangle, Arrow, NumberPlane, VGroup
- Animations: Write, FadeIn, FadeOut, Create, Transform, MoveToTarget, GrowArrow
- Duration: self.wait() calls should total ~30 seconds of animation
- No external images or assets
- The code must run with: manim -pql scene_{scene_id}.py Scene{scene_id}

Visual description:
{visual_description}

Scene title: {title}

Return ONLY the Python code, no explanation, no markdown fences."""

REVIEWER_PROMPT = """Review this Manim Community Edition code for correctness.
Check for:
1. Correct imports (from manim import *)
2. Valid class name matching Scene{scene_id}
3. Valid Manim API calls (no hallucinated methods)
4. No syntax errors
5. Self-contained (no external files)

If the code is correct, reply with: APPROVED
If there are issues, reply with: FIX NEEDED
Then list the exact issues and provide the corrected full code.

Code to review:
{code}"""

MANIM_TEMPLATE = """from manim import *

{code}
"""


def call_ollama(prompt: str, model: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 2048},
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
    response.raise_for_status()
    return response.json().get("response", "")


def extract_code(text: str) -> str:
    """Strip markdown fences and extract Python code."""
    text = re.sub(r"```(?:python)?", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def render_manim(scene_file: str, class_name: str, output_dir: str) -> tuple[bool, str]:
    """Attempt to render a Manim scene. Returns (success, error_message)."""
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


def generate_fallback_scene(scene_id: int, title: str, output_dir: str) -> str:
    """Use a pre-built topic-specific animated scene; generic text fallback if none exists."""
    from agents.prebuilt_scenes import PREBUILT_SCENES

    class_name = f"Scene{scene_id}"

    if scene_id in PREBUILT_SCENES:
        code = PREBUILT_SCENES[scene_id]
        print(f"  Using pre-built animated scene for scene {scene_id}.")
    else:
        # Generic animated fallback with title + bullet points
        code = f"""from manim import *

class {class_name}(Scene):
    def construct(self):
        title = Text("{title}", font_size=42, color=BLUE).to_edge(UP, buff=0.4)
        self.play(Write(title))
        self.wait(0.5)

        lines = VGroup(
            Text("Key concepts:", font_size=28, color=YELLOW),
            Text("AI-driven educational video generation", font_size=24),
            Text("Multi-agent pipeline architecture", font_size=24),
            Text("Open-source tools for Indian educators", font_size=24),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(ORIGIN + DOWN * 0.3)

        for line in lines:
            self.play(FadeIn(line, shift=RIGHT * 0.2), run_time=0.45)
            self.wait(0.3)

        self.wait(2)
        self.play(FadeOut(VGroup(title, lines)))
"""
        print(f"  Using generic animated fallback for scene {scene_id}.")

    scene_file = os.path.join(output_dir, f"scene_{scene_id}.py")
    with open(scene_file, "w") as f:
        f.write(code)
    return scene_file


def _find_rendered_mp4(class_name: str, search_root: str) -> str | None:
    """Walk search_root to find a rendered MP4 matching class_name."""
    for root, _, files in os.walk(search_root):
        for fname in files:
            if fname == f"{class_name}.mp4":
                return os.path.join(root, fname)
    return None


def generate_scene(scene: dict, scenes_dir: str) -> str | None:
    """
    Generate and render a Manim scene.
    Priority order:
    1. Dynamic templates (if scene_type is present) - for transcript-based content
    2. Pre-built topic-specific scenes (if scene_id in PREBUILT_SCENES) - legacy
    3. LLM Writer+Reviewer loop
    4. Generic animated fallback
    Returns path to rendered MP4 or None on failure.
    """
    scene_id = scene["scene_id"]
    title = scene["title"]
    visual_desc = scene["visual_description"]
    class_name = f"Scene{scene_id}"
    scene_file = os.path.join(scenes_dir, f"scene_{scene_id}.py")

    print(f"\n[Animation Agent] Scene {scene_id}: {title}")

    # ── Priority 1: Dynamic templates (for transcript-based scripts) ────────
    scene_type = scene.get("scene_type")
    if scene_type:
        try:
            from agents.scene_templates import generate_scene_code, SCENE_TEMPLATES
            if scene_type in SCENE_TEMPLATES:
                print(f"  Using dynamic template: {scene_type}")
                code = generate_scene_code(scene)
                if code:
                    with open(scene_file, "w") as f:
                        f.write(code)
                    success, err = render_manim(
                        scene_file, class_name, os.path.dirname(scenes_dir)
                    )
                    if success:
                        mp4 = _find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
                        if mp4:
                            print(f"  Dynamic template rendered: {mp4}")
                            return mp4
                    print(f"  Template render failed ({err[-150:]}). Trying fallbacks.")
        except ImportError:
            pass  # scene_templates not available, continue with fallbacks
    # ────────────────────────────────────────────────────────────────────────

    # ── Priority 2: Use pre-built animated scene if available (legacy) ──────
    from agents.prebuilt_scenes import PREBUILT_SCENES
    if scene_id in PREBUILT_SCENES:
        print(f"  Using pre-built animated scene.")
        pb_file = generate_fallback_scene(scene_id, title, scenes_dir)
        success, err = render_manim(pb_file, class_name, os.path.dirname(scenes_dir))
        if success:
            mp4 = _find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
            if mp4:
                print(f"  Pre-built scene rendered: {mp4}")
                return mp4
        print(f"  Pre-built render failed ({err[-200:]}). Falling back to LLM.")
    # ────────────────────────────────────────────────────────────────────────

    # ── Priority 2: LLM Writer+Reviewer loop ─────────────────────────────────
    print(f"  Attempting LLM-generated scene...")
    code = None
    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  Attempt {attempt}/{MAX_RETRIES}")

        writer_prompt = WRITER_PROMPT.format(
            scene_id=scene_id,
            visual_description=visual_desc,
            title=title,
        )
        if attempt > 1 and code:
            writer_prompt += f"\n\nPrevious attempt failed with this error:\n{last_error}\nFix the code."

        raw_code = call_ollama(writer_prompt, WRITER_MODEL)
        code = extract_code(raw_code)

        if "from manim import" not in code:
            code = "from manim import *\n\n" + code

        reviewer_prompt = REVIEWER_PROMPT.format(scene_id=scene_id, code=code)
        review = call_ollama(reviewer_prompt, REVIEWER_MODEL)

        if "FIX NEEDED" in review.upper():
            fixed = extract_code(review)
            if len(fixed) > 50 and "class" in fixed:
                code = fixed
            print(f"  Reviewer requested fixes.")

        with open(scene_file, "w") as f:
            f.write(code)

        success, last_error = render_manim(scene_file, class_name, os.path.dirname(scenes_dir))
        if success:
            print(f"  LLM scene rendered successfully.")
            mp4 = _find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
            if mp4:
                return mp4

    # ── Priority 3: Generic animated fallback ────────────────────────────────
    print(f"  All LLM attempts failed. Using animated fallback scene.")
    fallback_file = generate_fallback_scene(scene_id, title, scenes_dir)
    success, _ = render_manim(fallback_file, class_name, os.path.dirname(scenes_dir))
    if success:
        return _find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
    return None


def generate_all_scenes(script_path: str, scenes_dir: str) -> list[dict]:
    """Generate animations for all scenes in the script. Returns scene list with mp4_path."""
    with open(script_path) as f:
        script = json.load(f)

    os.makedirs(scenes_dir, exist_ok=True)
    results = []

    for scene in script["scenes"]:
        mp4_path = generate_scene(scene, scenes_dir)
        results.append({**scene, "mp4_path": mp4_path})

    print(f"\n[Animation Agent] Done. {sum(1 for r in results if r['mp4_path'])} / {len(results)} scenes rendered.")
    return results


if __name__ == "__main__":
    script = sys.argv[1] if len(sys.argv) > 1 else "output/script.json"
    scenes_dir = sys.argv[2] if len(sys.argv) > 2 else "output/scenes"
    generate_all_scenes(script, scenes_dir)
