"""
Agent 2: Animation Code Agent
Converts visual scene descriptions into Manim Community Edition Python code,
renders each scene to MP4. Uses a Writer+Reviewer retry loop for reliability.
Inspired by: github.com/makefinks/manim-generator
"""

import json
import os
import sys

from core.ollama_client import call_ollama
from core.llm_utils import extract_code
from core.config import (
    ANIMATION_MODEL, REVIEWER_MODEL, TIMEOUT_LONG,
    MAX_RETRIES, ENABLE_SELF_REFINE, QUALITY_THRESHOLD, MAX_REFINE_ITERATIONS,
)
from prompts.animation_prompts import WRITER_PROMPT, REVIEWER_PROMPT
from agents.rendering import render_manim, find_rendered_mp4

WRITER_MODEL = ANIMATION_MODEL


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


def generate_scene(
    scene: dict,
    scenes_dir: str,
    feedback: str | None = None
) -> str | None:
    """
    Generate and render a Manim scene.
    Priority order:
    1. Dynamic templates (if scene_type is present) - for transcript-based content
    2. Pre-built topic-specific scenes (if scene_id in PREBUILT_SCENES) - legacy
    3. LLM Writer+Reviewer loop
    4. Generic animated fallback

    Args:
        scene: Scene dict with scene_id, title, visual_description, etc.
        scenes_dir: Directory to save scene Python files.
        feedback: Optional feedback from previous iterations (for self-refine loop).
                  Contains issues and suggestions to address.

    Returns:
        Path to rendered MP4 or None on failure.
    """
    scene_id = scene["scene_id"]
    title = scene["title"]
    visual_desc = scene["visual_description"]
    class_name = f"Scene{scene_id}"
    scene_file = os.path.join(scenes_dir, f"scene_{scene_id}.py")

    print(f"\n[Animation Agent] Scene {scene_id}: {title}")

    scene_type = scene.get("scene_type")

    # ── Priority 1: TEMPLATES FIRST (guaranteed safe layout) ────────────────
    # Templates have pre-validated positioning that ALWAYS works
    if scene_type:
        try:
            from agents.scene_templates import generate_scene_code, SCENE_TEMPLATES
            from agents.scene_wrapper import process_manim_code
            if scene_type in SCENE_TEMPLATES:
                print(f"  Using SAFE template: {scene_type}")
                code = generate_scene_code(scene)
                if code:
                    # Apply safety wrapper even to templates for extra protection
                    code = process_manim_code(code)
                    with open(scene_file, "w") as f:
                        f.write(code)
                    success, err = render_manim(
                        scene_file, class_name, os.path.dirname(scenes_dir)
                    )
                    if success:
                        mp4 = find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
                        if mp4:
                            print(f"  Template rendered: {mp4}")
                            return mp4
                    print(f"  Template render failed ({err[-150:]}). Trying dynamic.")
        except ImportError as e:
            print(f"  Templates not available ({e}). Trying dynamic generator.")

    # ── Priority 2: Dynamic LLM generation (with aggressive safety wrapper) ──
    if scene_type:
        try:
            from agents.dynamic_scene_generator import generate_dynamic_scene
            print(f"  Using dynamic LLM generator: {scene_type}")
            mp4 = generate_dynamic_scene(scene, scenes_dir, feedback=feedback)
            if mp4:
                return mp4
            print(f"  Dynamic generator failed. Trying other fallbacks.")
        except ImportError as e:
            print(f"  Dynamic generator not available ({e}).")
    # ────────────────────────────────────────────────────────────────────────

    # ── Priority 2: Use pre-built animated scene if available (legacy) ──────
    from agents.prebuilt_scenes import PREBUILT_SCENES
    if scene_id in PREBUILT_SCENES:
        print(f"  Using pre-built animated scene.")
        pb_file = generate_fallback_scene(scene_id, title, scenes_dir)
        success, err = render_manim(pb_file, class_name, os.path.dirname(scenes_dir))
        if success:
            mp4 = find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
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

        # Inject feedback from self-refine loop (quality issues from previous iterations)
        if feedback:
            writer_prompt += f"\n\n{feedback}"

        if attempt > 1 and code:
            writer_prompt += f"\n\nPrevious attempt failed with this error:\n{last_error}\nFix the code."

        raw_code = call_ollama(writer_prompt, model=WRITER_MODEL, timeout=TIMEOUT_LONG, temperature=0.2)
        code = extract_code(raw_code)

        if "from manim import" not in code:
            code = "from manim import *\n\n" + code

        reviewer_prompt = REVIEWER_PROMPT.format(scene_id=scene_id, code=code)
        review = call_ollama(reviewer_prompt, model=REVIEWER_MODEL, timeout=TIMEOUT_LONG, temperature=0.2)

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
            mp4 = find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
            if mp4:
                return mp4

    # ── Priority 3: Generic animated fallback ────────────────────────────────
    print(f"  All LLM attempts failed. Using animated fallback scene.")
    fallback_file = generate_fallback_scene(scene_id, title, scenes_dir)
    success, _ = render_manim(fallback_file, class_name, os.path.dirname(scenes_dir))
    if success:
        return find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
    return None


def generate_all_scenes(script_path: str, scenes_dir: str) -> list[dict]:
    """
    Generate animations for all scenes in the script with per-scene evaluation.

    When ENABLE_SELF_REFINE is True (default), each scene goes through a
    Generate → Evaluate → Feedback → Refine loop until it passes the quality
    threshold or max iterations are reached.

    Returns:
        List of scene dicts with mp4_path and quality_score added.
    """
    with open(script_path) as f:
        script = json.load(f)

    os.makedirs(scenes_dir, exist_ok=True)
    results = []
    evaluations = []

    # Use self-refine loop if enabled
    if ENABLE_SELF_REFINE:
        try:
            from agents.evaluation import (
                generate_with_self_refine,
                evaluate_all_scenes_summary,
            )
            use_self_refine = True
            print(f"\n[Animation Agent] Self-refine enabled (threshold: {QUALITY_THRESHOLD})")
        except ImportError:
            use_self_refine = False
            print("\n[Animation Agent] Self-refine disabled (agents.evaluation not found)")
    else:
        use_self_refine = False
        print("\n[Animation Agent] Self-refine disabled by config")

    for scene in script["scenes"]:
        scene_id = scene["scene_id"]

        if use_self_refine:
            # Use self-refine loop for quality assurance
            mp4_path, eval_result = generate_with_self_refine(
                scene=scene,
                scenes_dir=scenes_dir,
                generate_fn=generate_scene,
                threshold=QUALITY_THRESHOLD,
                max_iter=MAX_REFINE_ITERATIONS,
            )
            evaluations.append(eval_result)
            results.append({
                **scene,
                "mp4_path": mp4_path,
                "quality_score": eval_result.overall_score,
                "passed_threshold": eval_result.passed_threshold,
            })
        else:
            # Direct generation without evaluation loop
            mp4_path = generate_scene(scene, scenes_dir)
            results.append({**scene, "mp4_path": mp4_path})

    # Print summary
    rendered = sum(1 for r in results if r.get("mp4_path"))
    print(f"\n[Animation Agent] Done. {rendered}/{len(results)} scenes rendered.")

    if use_self_refine and evaluations:
        summary = evaluate_all_scenes_summary(evaluations)
        print(f"  Quality: {summary['avg_score']} avg, {summary['passed']}/{summary['total_scenes']} passed")

    return results


if __name__ == "__main__":
    script = sys.argv[1] if len(sys.argv) > 1 else "output/script.json"
    scenes_dir = sys.argv[2] if len(sys.argv) > 2 else "output/scenes"
    generate_all_scenes(script, scenes_dir)
