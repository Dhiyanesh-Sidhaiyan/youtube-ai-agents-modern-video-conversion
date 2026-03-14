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

# Reuse shared utilities from animation_agent to avoid duplication
from agents.animation_agent import (
    call_ollama,
    extract_code,
    render_manim,
    _find_rendered_mp4,
    WRITER_MODEL,
    MAX_RETRIES,
    OLLAMA_TIMEOUT,
)

# Import code validator for pre-render validation
from agents.code_validator import validate_manim_code, auto_fix_code

# Import layout system for positioning rules
from agents.layout_system import LAYOUT_RULES_PROMPT

# Import layout validator for pre-render layout checks
from agents.layout_validator import validate_layout

# Import scene wrapper for automatic safety layer
from agents.scene_wrapper import process_manim_code

# ─── Prompts ────────────────────────────────────────────────────────────────

INTRO_HOOK_PROMPT = """You are a master public speaker creating a video hook.

TOPIC: {topic}
KEY CONCEPTS: {key_concepts}
SUMMARY: {summary}

Generate an attention-grabbing intro hook. Choose the best style for this topic:

1. QUESTION: Start with a thought-provoking question
   Example: "What if I told you that 90% of AI projects fail in production?"

2. STATISTIC: Lead with a surprising number
   Example: "In 2024, AI processes over 100 trillion requests daily."

3. SCENARIO: Create a relatable situation
   Example: "Imagine you're a student trying to learn at 2 AM with no textbooks..."

4. BOLD CLAIM: Make a compelling statement
   Example: "This concept will revolutionize how you think about education forever."

Return ONLY valid JSON, no markdown, no explanation:
{{
  "hook_type": "question",
  "hook_text": "The actual hook text (max 15 words)",
  "supporting_points": ["point1", "point2", "point3"],
  "visual_style": "dramatic"
}}"""


OUTRO_HOOK_PROMPT = """You are a master public speaker creating a memorable conclusion.

TOPIC: {topic}
INTRO HOOK: {intro_hook}
KEY TAKEAWAYS: {takeaways}

Generate a powerful conclusion that:
1. Callbacks to the intro hook (creates closure for the audience)
2. Summarizes the single most important insight
3. Ends with a concrete call-to-action

Return ONLY valid JSON, no markdown, no explanation:
{{
  "callback_text": "Reference to intro hook (max 15 words)",
  "key_insight": "The ONE thing to remember (max 12 words)",
  "call_to_action": "What viewer should do next (max 12 words)",
  "final_words": "Memorable closing phrase (5-8 words)"
}}"""


DYNAMIC_MANIM_PROMPT = """You are a Manim Community Edition expert creating an impressive animated scene.

TOPIC: {topic}
SCENE TYPE: {scene_type}
SCENE TITLE: {title}
HOOK TEXT: {hook_text}
VISUAL STYLE: {visual_style}
CLASS NAME: Scene{scene_id}

{feedback_section}

""" + LAYOUT_RULES_PROMPT + """

STRICT REQUIREMENTS:
1. Start with: from manim import *
2. Class name must be exactly: Scene{scene_id}
3. Dark background: Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
   Always add it with self.add(bg) before any animations
4. Use ONLY these safe animations: Write, FadeIn, GrowFromCenter, Flash, LaggedStart, Indicate, Circumscribe, Transform
5. End with self.wait(3) — NO FadeOut at the very end (hold final frame)
6. Total run time ~25-35 seconds
7. No external image files or assets
8. All Text must have font_size between 20 and 52

CRITICAL MANIM RULES (violating these causes render failures):
- For Text objects: ONLY use Write() or FadeIn(). NEVER use Create() or DrawBorderThenFill() on Text.
- Create() and DrawBorderThenFill() ONLY work on VMobjects like Circle, Rectangle, Line, Arrow, Polygon.
- LaggedStart MUST receive animation instances, NOT classes. CORRECT: LaggedStart(*[FadeIn(t) for t in texts])
  WRONG: LaggedStart(FadeIn, texts) or LaggedStart(*texts)
- Text has NO method 'to_center'. Use .move_to(ORIGIN) or .center() instead.
- Always instantiate animations: self.play(FadeIn(obj)) NOT self.play(FadeIn)
- ALL Manim parameters use snake_case, NEVER camelCase:
  CORRECT: RoundedRectangle(corner_radius=0.3, fill_color=BLUE, fill_opacity=0.8)
  WRONG: RoundedRectangle(cornerRadius=0.3, fillColor=BLUE, fillOpacity=0.8)
- NEVER use ShowCreation - it does not exist! Use Create() instead.
- AnimationGroup has NO .repeat() method. To repeat, use a loop: for _ in range(n): self.play(anim)
- Use color CONSTANTS (WHITE, BLUE, RED, YELLOW, GREEN) or hex strings ('#ffffff'), NOT RGB tuples.

{scene_type_instructions}

Return ONLY the Python code, no markdown fences, no explanation."""


INTRO_INSTRUCTIONS = """For INTRO scenes:
EXACT LAYOUT PATTERN (follow precisely):
```
title = Text("Title", font_size=42, color=WHITE)
title.to_edge(UP, buff=0.5)

hook = Text("Hook text", font_size=32, color=YELLOW)
hook.next_to(title, DOWN, buff=0.6)

points = VGroup(
    Text("• Point 1", font_size=26),
    Text("• Point 2", font_size=26),
    Text("• Point 3", font_size=26),
)
points.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
points.next_to(hook, DOWN, buff=0.5)
points.scale_to_fit_width(min(11, points.get_width()))
```
- First animation: GrowFromCenter on title, then Flash(title, color=YELLOW)
- Use LaggedStart: LaggedStart(*[FadeIn(p) for p in points], lag_ratio=0.3)
- For ALL Text animations, use Write(text) or FadeIn(text) only"""


CONCLUSION_INSTRUCTIONS = """For CONCLUSION scenes:
EXACT LAYOUT PATTERN (follow precisely):
```
# Header at top
header = Text("Key Takeaways", font_size=40, color=GOLD)
header.to_edge(UP, buff=0.5)

# Takeaway points - MUST use VGroup + arrange
takeaways = VGroup(
    Text("✓ Takeaway 1", font_size=26, color=GREEN),
    Text("✓ Takeaway 2", font_size=26, color=GREEN),
    Text("✓ Takeaway 3", font_size=26, color=GREEN),
)
takeaways.arrange(DOWN, aligned_edge=LEFT, buff=0.35)
takeaways.next_to(header, DOWN, buff=0.6)

# Call-to-action box at bottom
cta_box = RoundedRectangle(width=10, height=1.2, corner_radius=0.2, fill_color=BLUE, fill_opacity=0.3)
cta_text = Text("Call to action here", font_size=28, color=WHITE)
cta_group = VGroup(cta_box, cta_text)
cta_text.move_to(cta_box.get_center())
cta_group.to_edge(DOWN, buff=0.8)

# Scale if needed
if takeaways.get_width() > 11:
    takeaways.scale_to_fit_width(11)
```
- Use LaggedStart: LaggedStart(*[FadeIn(t) for t in takeaways], lag_ratio=0.4)
- Use GrowFromCenter for shapes, Write() for text
- For ALL Text animations, use Write(text) or FadeIn(text) only"""


CONCEPT_INSTRUCTIONS = """For CONCEPT explanation scenes:
EXACT LAYOUT PATTERN (follow precisely):
```
# Title at top
title = Text("Concept Name", font_size=40, color=BLUE)
title.to_edge(UP, buff=0.5)

# Divider line
line = Line(LEFT * 4, RIGHT * 4, color=BLUE_B)
line.next_to(title, DOWN, buff=0.2)

# Bullet points - MUST use VGroup + arrange
bullets = VGroup(
    Text("• Point 1", font_size=26, color=WHITE),
    Text("• Point 2", font_size=26, color=WHITE),
    Text("• Point 3", font_size=26, color=WHITE),
)
bullets.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
bullets.next_to(line, DOWN, buff=0.5)
bullets.to_edge(LEFT, buff=1.5)

# Scale if too wide
if bullets.get_width() > 5:
    bullets.scale_to_fit_width(5)
```
- Create main visual on right side if needed
- Use LaggedStart: LaggedStart(*[FadeIn(p) for p in bullets], lag_ratio=0.3)
- For ALL Text animations, use Write(text) or FadeIn(text) only"""


COMPARISON_INSTRUCTIONS = """For COMPARISON scenes (X vs Y):
EXACT LAYOUT PATTERN (follow precisely):
```
# Title at top
title = Text("X vs Y", font_size=38, color=WHITE)
title.to_edge(UP, buff=0.5)

# Center divider
divider = Line(UP * 2.5, DOWN * 2.5, color=WHITE, stroke_width=2)
divider.next_to(title, DOWN, buff=0.4)

# Left column - BLUE items
left_items = VGroup(
    Text("• Left 1", font_size=24, color=BLUE),
    Text("• Left 2", font_size=24, color=BLUE),
)
left_items.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
left_items.next_to(divider, LEFT, buff=0.8)
left_items.align_to(divider, UP)

# Right column - GREEN items
right_items = VGroup(
    Text("• Right 1", font_size=24, color=GREEN),
    Text("• Right 2", font_size=24, color=GREEN),
)
right_items.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
right_items.next_to(divider, RIGHT, buff=0.8)
right_items.align_to(divider, UP)

# Scale columns if too wide
for col in [left_items, right_items]:
    if col.get_width() > 5:
        col.scale_to_fit_width(5)
```
- Use LaggedStart: LaggedStart(*[FadeIn(i) for i in left_items], lag_ratio=0.4)
- For ALL Text animations, use Write(text) or FadeIn(text) only"""


PROCESS_INSTRUCTIONS = """For PROCESS/FLOW scenes:
EXACT LAYOUT PATTERN (follow precisely):
```
# Title at top
title = Text("Process Title", font_size=38, color=WHITE)
title.to_edge(UP, buff=0.5)

# Create steps as a horizontal group
step1_circle = Circle(radius=0.4, color=BLUE, fill_opacity=0.8)
step1_num = Text("1", font_size=24, color=WHITE)
step1 = VGroup(step1_circle, step1_num)
step1_num.move_to(step1_circle.get_center())

step2_circle = Circle(radius=0.4, color=BLUE, fill_opacity=0.8)
step2_num = Text("2", font_size=24, color=WHITE)
step2 = VGroup(step2_circle, step2_num)
step2_num.move_to(step2_circle.get_center())

step3_circle = Circle(radius=0.4, color=BLUE, fill_opacity=0.8)
step3_num = Text("3", font_size=24, color=WHITE)
step3 = VGroup(step3_circle, step3_num)
step3_num.move_to(step3_circle.get_center())

# Arrange steps horizontally
steps = VGroup(step1, step2, step3)
steps.arrange(RIGHT, buff=1.5)
steps.next_to(title, DOWN, buff=1.0)

# Add arrows between steps
arrow1 = Arrow(step1.get_right(), step2.get_left(), buff=0.1, color=WHITE)
arrow2 = Arrow(step2.get_right(), step3.get_left(), buff=0.1, color=WHITE)

# Scale if too wide
all_content = VGroup(steps, arrow1, arrow2)
if all_content.get_width() > 11:
    all_content.scale_to_fit_width(11)
```
- Animate: GrowFromCenter for shapes, then Write for text
- For ALL Text animations, use Write(text) or FadeIn(text) only"""


EXAMPLE_INSTRUCTIONS = """For EXAMPLE demonstration scenes:
EXACT LAYOUT PATTERN (follow precisely):
```
# Title at top
title = Text("Example: Topic", font_size=36, color=YELLOW)
title.to_edge(UP, buff=0.5)

# Code block container
code_box = RoundedRectangle(width=10, height=2.5, corner_radius=0.2,
                            fill_color="#2d2d2d", fill_opacity=0.9, stroke_color=WHITE)
code_box.next_to(title, DOWN, buff=0.5)

# Code/input text inside box
input_text = Text("input_code_here", font_size=22, color=BLUE_A)
input_text.move_to(code_box.get_center())

# Arrow pointing down
arrow = Arrow(UP * 0.3, DOWN * 0.3, color=WHITE)
arrow.next_to(code_box, DOWN, buff=0.3)

# Result box
result_box = RoundedRectangle(width=10, height=1.5, corner_radius=0.2,
                              fill_color="#1a3a1a", fill_opacity=0.9, stroke_color=GREEN)
result_box.next_to(arrow, DOWN, buff=0.3)

result_text = Text("Result: output", font_size=24, color=GREEN_A)
result_text.move_to(result_box.get_center())

# Group and scale
all_content = VGroup(code_box, input_text, arrow, result_box, result_text)
if all_content.get_height() > 5.5:
    all_content.scale_to_fit_height(5.5)
```
- Use Indicate() or Flash() to highlight key parts
- For ALL Text animations, use Write(text) or FadeIn(text) only"""


# Map scene types to their instructions
SCENE_TYPE_INSTRUCTIONS = {
    "intro": INTRO_INSTRUCTIONS,
    "conclusion": CONCLUSION_INSTRUCTIONS,
    "concept": CONCEPT_INSTRUCTIONS,
    "comparison": COMPARISON_INSTRUCTIONS,
    "process": PROCESS_INSTRUCTIONS,
    "example": EXAMPLE_INSTRUCTIONS,
}


# ─── LLM Helpers ────────────────────────────────────────────────────────────

def _call_ollama_json(prompt: str) -> dict:
    """Call Ollama and parse JSON response. Returns empty dict on failure."""
    raw = call_ollama(prompt, WRITER_MODEL)
    # Strip markdown fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON object from response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}


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
    result = _call_ollama_json(prompt)

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
    result = _call_ollama_json(prompt)

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
    raw = call_ollama(prompt, WRITER_MODEL)
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
            mp4 = _find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
            if mp4:
                print(f"  [Dynamic Generator] Success: {mp4}")
                return mp4
            last_error = "Render succeeded but MP4 file not found"

        print(f"  [Dynamic Generator] Attempt {attempt} failed: {last_error[-200:]}")

    print(f"  [Dynamic Generator] All {MAX_RETRIES} attempts failed.")
    return None
