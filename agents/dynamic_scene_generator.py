"""
Dynamic Scene Generator
Generates impressive intro/conclusion animations like a master public speaker.
Uses LLM to create topic-specific hooks and full Manim code.

Hook types for intro:
  question   - "Have you ever wondered...?"
  statistic  - "Did you know that 80% of..."
  scenario   - "Imagine you're..."
  bold_claim - "This will change how you..."

Outro styles:
  callback + call_to_action + key_insight
"""

import json
import os
import re

from core.ollama_client import call_ollama
from core.llm_utils import extract_code, extract_json
from core.config import ANIMATION_MODEL, MAX_RETRIES, TIMEOUT_LONG
from agents.rendering import render_manim, find_rendered_mp4

# Import code validator for pre-render validation
from agents.code_validator import validate_manim_code, auto_fix_code

# Import layout validator for pre-render layout checks
from agents.layout_validator import validate_layout

# Import scene wrapper for automatic safety layer
from agents.scene_wrapper import process_manim_code

# Import prompts from dedicated module
from prompts.scene_gen_prompts import (
    INTRO_HOOK_PROMPT,
    OUTRO_HOOK_PROMPT,
    DYNAMIC_MANIM_PROMPT,
    SCENE_TYPE_INSTRUCTIONS,
    CONCEPT_INSTRUCTIONS,
)

WRITER_MODEL = ANIMATION_MODEL


# ─── Public API ─────────────────────────────────────────────────────────────

def generate_intro_hook(topic: str, key_concepts: list, summary: str) -> dict:
    """
    Generate an attention-grabbing intro hook via LLM.

    Returns dict with keys: hook_type, hook_text, supporting_points, visual_style.
    Falls back to safe defaults if LLM fails.
    """
    prompt = INTRO_HOOK_PROMPT.format(
        topic=topic,
        key_concepts=", ".join(key_concepts[:6]) if key_concepts else "key ideas",
        summary=summary[:300] if summary else topic,
    )
    print(f"  [Dynamic Generator] Generating intro hook...")
    result = extract_json(call_ollama(prompt, model=WRITER_MODEL, timeout=TIMEOUT_LONG)) or {}

    # Safe defaults
    hook = {
        "hook_type": result.get("hook_type", "question"),
        "hook_text": result.get("hook_text", f"What do you really know about {topic}?"),
        "supporting_points": result.get("supporting_points", key_concepts[:3] if key_concepts else [topic]),
        "visual_style": result.get("visual_style", "dramatic"),
    }
    print(f"  [Dynamic Generator] Hook type: {hook['hook_type']}")
    print(f"  [Dynamic Generator] Hook: \"{hook['hook_text']}\"")
    return hook


def generate_outro_hook(topic: str, takeaways: list, intro_hook: str) -> dict:
    """
    Generate a memorable conclusion with callback to intro hook.

    Returns dict with keys: callback_text, key_insight, call_to_action, final_words.
    Falls back to safe defaults if LLM fails.
    """
    prompt = OUTRO_HOOK_PROMPT.format(
        topic=topic,
        intro_hook=intro_hook or f"our opening question about {topic}",
        takeaways=", ".join(takeaways[:4]) if takeaways else topic,
    )
    print(f"  [Dynamic Generator] Generating outro hook...")
    result = extract_json(call_ollama(prompt, model=WRITER_MODEL, timeout=TIMEOUT_LONG)) or {}

    hook = {
        "callback_text": result.get("callback_text", f"Now you have the answer about {topic}"),
        "key_insight": result.get("key_insight", f"Understanding {topic} changes everything"),
        "call_to_action": result.get("call_to_action", "Apply what you learned today"),
        "final_words": result.get("final_words", "Start your journey now"),
    }
    print(f"  [Dynamic Generator] Outro callback: \"{hook['callback_text']}\"")
    return hook


def generate_dynamic_manim_code(scene: dict, hook: dict | None = None, feedback: str | None = None) -> str:
    """
    Generate complete Manim code for ANY scene type using LLM.

    Args:
        scene: Scene dict (scene_id, scene_type, title, narration_text, key_concepts, etc.)
        hook:  Optional hook dict (required for intro/conclusion, ignored for other types)
        feedback: Optional quality feedback from self-refine loop

    Returns:
        Python source code string.
    """
    scene_type = scene.get("scene_type", "concept")
    scene_id = scene["scene_id"]
    title = scene.get("title", "Topic")
    key_concepts = scene.get("key_concepts", [])
    visual_description = scene.get("visual_description", "")

    # Get scene-specific instructions
    scene_instructions = SCENE_TYPE_INSTRUCTIONS.get(scene_type, CONCEPT_INSTRUCTIONS)

    # Determine hook text and visual style based on scene type
    if scene_type == "intro" and hook:
        hook_text = hook.get("hook_text", "")
        visual_style = hook.get("visual_style", "dramatic")
    elif scene_type == "conclusion" and hook:
        hook_text = hook.get("callback_text", "")
        visual_style = "elegant"
    else:
        # For other scene types, use key concepts or visual description
        hook_text = ", ".join(key_concepts[:3]) if key_concepts else visual_description[:80]
        visual_style = "clean"

    # Build feedback section
    feedback_section = ""
    if feedback:
        feedback_section = f"PREVIOUS ATTEMPT FEEDBACK (fix these issues):\n{feedback}\n"

    # Add extra context for non-intro/conclusion scenes
    extra_context = ""
    if scene_type not in ("intro", "conclusion"):
        if key_concepts:
            extra_context += f"\nKEY CONCEPTS TO SHOW: {', '.join(key_concepts[:5])}"
        if visual_description:
            extra_context += f"\nVISUAL DESCRIPTION: {visual_description[:200]}"

    prompt = DYNAMIC_MANIM_PROMPT.format(
        topic=title,
        scene_type=scene_type,
        title=title[:45],
        hook_text=hook_text[:100] if hook_text else f"Explore {title}",
        visual_style=visual_style,
        scene_id=scene_id,
        feedback_section=feedback_section + extra_context,
        scene_type_instructions=scene_instructions,
    )

    print(f"  [Dynamic Generator] Generating Manim code for {scene_type} scene...")
    raw = call_ollama(prompt, model=WRITER_MODEL, timeout=TIMEOUT_LONG, temperature=0.2)
    code = extract_code(raw)

    # Ensure imports are present
    if "from manim import" not in code:
        code = "from manim import *\n\n" + code

    print(f"  [Dynamic Generator] Manim code generated ({len(code)} chars)")
    return code


def generate_dynamic_scene(
    scene: dict,
    scenes_dir: str,
    feedback: str = None,
) -> str | None:
    """
    Main entry point: generate and render ANY scene type dynamically using LLM.

    Flow:
      1. Generate hook (for intro/conclusion only)
      2. Generate Manim code with LLM + optional quality feedback
      3. Validate code BEFORE rendering (catches common mistakes)
      4. Write to scene_{scene_id}.py, render with manim -ql
      5. On render failure: retry up to MAX_RETRIES with error injected
      6. Return mp4_path on success, None on all failures

    The `feedback` param is passed by scene_evaluator.generate_with_self_refine()
    and contains quality issues (visual/technical). It is injected into the Manim
    prompt so the LLM addresses them in the next generation.

    Note: intro_hook text is stored in scene["_intro_hook"] so the conclusion
    scene can reference it for narrative callback.
    """
    scene_id = scene["scene_id"]
    scene_type = scene.get("scene_type", "concept")
    title = scene.get("title", "Topic")
    class_name = f"Scene{scene_id}"
    scene_file = os.path.join(scenes_dir, f"scene_{scene_id}.py")
    os.makedirs(scenes_dir, exist_ok=True)

    # Extract context for hook generation
    key_concepts = scene.get("key_concepts", [])
    narration = scene.get("narration_text", "")

    # ── Generate hook (only for intro/conclusion) ─────────────────────────
    hook = None
    if scene_type == "intro":
        hook = generate_intro_hook(topic=title, key_concepts=key_concepts, summary=narration)
        # Store hook text for conclusion callback
        scene["_intro_hook"] = hook.get("hook_text", "")
    elif scene_type == "conclusion":
        # Conclusion: try to use the stored intro hook for callback
        intro_hook_ref = scene.get("_intro_hook", "")
        takeaways = key_concepts or [title]
        hook = generate_outro_hook(topic=title, takeaways=takeaways, intro_hook=intro_hook_ref)
    # For other scene types (concept, comparison, process, example), hook is None

    # ── Generate + Validate + Render loop ─────────────────────────────────
    last_error = ""
    validation_feedback = ""

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  [Dynamic Generator] Render attempt {attempt}/{MAX_RETRIES}...")

        # Inject quality feedback, validation errors, and render errors
        combined_feedback = feedback or ""
        if validation_feedback:
            combined_feedback = (
                (combined_feedback + "\n\n" if combined_feedback else "") +
                validation_feedback
            )
        if attempt > 1 and last_error:
            combined_feedback = (
                (combined_feedback + "\n\n" if combined_feedback else "") +
                f"Previous render error (fix this):\n{last_error[-1500:]}"
            )

        code = generate_dynamic_manim_code(scene, hook, feedback=combined_feedback or None)

        # ── Apply safety wrapper (auto-scaling, position fixes) ───────────
        code = process_manim_code(code)
        print("  [Dynamic Generator] Applied safety wrapper to code")

        # ── Pre-render validation ──────────────────────────────────────────
        validation = validate_manim_code(code, scene_id)
        if not validation.valid:
            print(f"  [Dynamic Generator] Code validation failed ({len(validation.get_critical_issues())} critical issues)")
            # Try auto-fix
            code = auto_fix_code(code, validation.issues)
            # Re-validate after auto-fix
            validation = validate_manim_code(code, scene_id)
            if not validation.valid:
                # Still invalid - add to feedback for next attempt
                validation_feedback = validation.format_feedback()
                print("  [Dynamic Generator] Auto-fix insufficient, retrying with feedback...")
                continue
        else:
            validation_feedback = ""  # Clear validation feedback on success
            # Log warnings if any
            warnings = validation.get_warnings()
            if warnings:
                print(f"  [Dynamic Generator] Code has {len(warnings)} warnings (non-critical)")

        # ── Layout validation ─────────────────────────────────────────────
        layout_result = validate_layout(code)
        if not layout_result.valid:
            print(f"  [Dynamic Generator] Layout validation failed ({len(layout_result.get_critical_issues())} critical issues)")
            # Add layout feedback for next attempt
            layout_feedback = layout_result.format_feedback()
            validation_feedback = (
                (validation_feedback + "\n\n" if validation_feedback else "") +
                layout_feedback
            )
            print("  [Dynamic Generator] Layout issues detected, retrying with feedback...")
            continue
        elif layout_result.issues:
            # Non-critical layout warnings
            print(f"  [Dynamic Generator] Layout has {len(layout_result.get_warnings())} warnings")

        with open(scene_file, "w") as f:
            f.write(code)

        success, last_error = render_manim(scene_file, class_name, os.path.dirname(scenes_dir))
        if success:
            mp4 = find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
            if mp4:
                print(f"  [Dynamic Generator] Success: {mp4}")
                return mp4
            last_error = "Render succeeded but MP4 file not found"

        print(f"  [Dynamic Generator] Attempt {attempt} failed: {last_error[-200:]}")

    print(f"  [Dynamic Generator] All {MAX_RETRIES} attempts failed.")
    return None
