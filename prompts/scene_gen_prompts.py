"""
prompts/scene_gen_prompts.py — LLM prompt templates for dynamic scene generation.

Extracted from agents/dynamic_scene_generator.py (lines 43–346):
  - INTRO_HOOK_PROMPT, OUTRO_HOOK_PROMPT, DYNAMIC_MANIM_PROMPT
  - Per-scene-type instruction blocks (intro, conclusion, concept, comparison,
    process, example) and the SCENE_TYPE_INSTRUCTIONS mapping.
"""

from agents.layout_system import LAYOUT_RULES_PROMPT

# ── Hook prompts ──────────────────────────────────────────────────────────────

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


# ── Main Manim generation prompt ──────────────────────────────────────────────

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


# ── Per-scene-type layout instructions ───────────────────────────────────────

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


# Mapping used by dynamic_scene_generator.generate_dynamic_manim_code()
SCENE_TYPE_INSTRUCTIONS = {
    "intro": INTRO_INSTRUCTIONS,
    "conclusion": CONCLUSION_INSTRUCTIONS,
    "concept": CONCEPT_INSTRUCTIONS,
    "comparison": COMPARISON_INSTRUCTIONS,
    "process": PROCESS_INSTRUCTIONS,
    "example": EXAMPLE_INSTRUCTIONS,
}
