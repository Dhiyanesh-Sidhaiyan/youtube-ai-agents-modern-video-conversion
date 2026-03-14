"""
Generic Parameterized Manim Scene Templates
These templates are used to dynamically generate Manim scenes based on content.
Each template type handles different visual presentations.
"""

import json
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
PARAM_EXTRACTOR_MODEL = "llama3"  # Faster model for param extraction
PARAM_EXTRACTOR_TIMEOUT = 45  # Increased timeout for better extraction
PARAM_EXTRACTOR_RETRY_TIMEOUT = 60  # Extended timeout for retries


# ─── Generic Content Detection & Fallback Helpers ───────────────────────────

def log_extraction_warning(scene_id: int, message: str):
    """Log warning about extraction issues for visibility."""
    print(f"  ⚠️  Scene {scene_id}: {message}")


def all_steps_generic(steps: list) -> bool:
    """
    Detect generic Step 1, Step 2, Step 3 patterns.
    Returns True if steps appear to be placeholder content.
    """
    if not steps:
        return True

    generic_patterns = [
        "Step 1", "Step 2", "Step 3", "Step 4", "Step 5",
        "First", "Second", "Third", "Fourth", "Fifth",
        "Point 1", "Point 2", "Point 3",
        "Feature A", "Feature B", "Feature C",
        "Item 1", "Item 2", "Item 3"
    ]

    generic_count = 0
    for step in steps:
        step_name = str(step[0]) if isinstance(step, (list, tuple)) and len(step) > 0 else str(step)
        step_desc = str(step[1]) if isinstance(step, (list, tuple)) and len(step) > 1 else ""

        # Check if step name matches generic patterns
        is_generic_name = any(g.lower() in step_name.lower() for g in generic_patterns)
        # Check if description is empty or too short
        is_empty_desc = len(step_desc.strip()) < 5

        if is_generic_name and is_empty_desc:
            generic_count += 1

    # If more than half are generic, consider it all generic
    return generic_count >= len(steps) / 2


def extract_steps_from_narration(narration: str, title: str = "") -> list:
    """
    Extract meaningful steps directly from narration text.
    Content-aware fallback when LLM extraction fails.
    """
    if not narration:
        return []

    steps = []

    # Try to find numbered patterns (1. xxx, 2. xxx)
    numbered_pattern = re.findall(r'(?:^|\. )(\d+)[.)\s]+([^.!?]+[.!?]?)', narration)
    if numbered_pattern and len(numbered_pattern) >= 2:
        for num, text in numbered_pattern[:5]:
            clean_text = text.strip()[:50]
            if len(clean_text) > 10:
                steps.append([f"Step {num}", clean_text])

    # Try "First..., Second..., Third..." patterns
    if not steps:
        ordinal_pattern = re.findall(
            r'\b(first|second|third|then|next|finally)[,\s]+([^.!?]+[.!?]?)',
            narration, re.IGNORECASE
        )
        ordinal_map = {"first": 1, "second": 2, "third": 3, "then": 4, "next": 5, "finally": 6}
        for ordinal, text in ordinal_pattern[:5]:
            clean_text = text.strip()[:50]
            if len(clean_text) > 10:
                idx = ordinal_map.get(ordinal.lower(), len(steps) + 1)
                steps.append([f"Step {idx}", clean_text])

    # Fallback: Split narration into key sentences
    if not steps:
        sentences = re.split(r'[.!?]+', narration)
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:4]

        for i, sentence in enumerate(meaningful_sentences, 1):
            # Extract first 3-4 words as step name
            words = sentence.split()[:4]
            step_name = ' '.join(words)[:15]
            step_desc = sentence[:50]
            steps.append([step_name, step_desc])

    # If still nothing, use title as single step
    if not steps and title:
        steps = [[title[:15], narration[:50] if narration else "Key concept"]]

    return steps if steps else [["Overview", "See visual demonstration"]]


def extract_bullet_points_from_narration(narration: str, count: int = 3) -> list:
    """
    Extract meaningful bullet points directly from narration.
    Used as fallback when LLM extraction fails.
    """
    if not narration:
        return ["See visual demonstration"]

    # Split into sentences
    sentences = re.split(r'[.!?]+', narration)
    meaningful = [s.strip() for s in sentences if len(s.strip()) > 15]

    # Take the most meaningful sentences (not too long, not too short)
    scored = []
    for s in meaningful:
        # Prefer medium-length sentences with keywords
        score = 0
        if 20 < len(s) < 80:
            score += 2
        if any(kw in s.lower() for kw in ['important', 'key', 'note', 'remember', 'main', 'first', 'second']):
            score += 1
        scored.append((score, s))

    scored.sort(reverse=True, key=lambda x: x[0])
    points = [s[:50] for _, s in scored[:count]]

    # Ensure we have enough points
    while len(points) < count and meaningful:
        for s in meaningful:
            if s[:50] not in points:
                points.append(s[:50])
                if len(points) >= count:
                    break

    return points if points else [narration[:50]]


def all_points_generic(points: list) -> bool:
    """Check if bullet points are generic placeholders."""
    if not points:
        return True

    generic_patterns = [
        "point 1", "point 2", "point 3",
        "key point 1", "key point 2",
        "feature a", "feature b",
        "item 1", "item 2"
    ]

    generic_count = sum(
        1 for p in points
        if any(g in str(p).lower() for g in generic_patterns)
    )
    return generic_count >= len(points) / 2


# ─── Scene Templates ────────────────────────────────────────────────────────

SCENE_TEMPLATES = {

    "intro": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark blue gradient background for better visibility
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Animated title with underline
        title = Text("{title}", font_size=44, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        underline = Line(
            title.get_left(), title.get_right(),
            color=BLUE, stroke_width=3
        ).next_to(title, DOWN, buff=0.1)

        self.play(
            GrowFromCenter(title),
            run_time=0.8
        )
        self.play(Create(underline), run_time=0.4)
        self.wait(0.3)

        # Subtitle with fade and shift
        subtitle = Text("{subtitle}", font_size=26, color=GREY_B).next_to(underline, DOWN, buff=0.4)
        self.play(FadeIn(subtitle, shift=UP * 0.3), run_time=0.5)
        self.wait(0.4)

        # Key points with staggered animation and icons
        points = VGroup(
{bullet_points_code}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(ORIGIN + DOWN * 0.3)

        # Add decorative bullets
        for i, point in enumerate(points):
            bullet = Dot(color=YELLOW, radius=0.08).next_to(point, LEFT, buff=0.15)
            self.play(
                GrowFromCenter(bullet),
                FadeIn(point, shift=RIGHT * 0.4),
                run_time=0.4
            )
            self.wait(0.2)

        # Hold final frame for freeze (no fade out)
        self.wait(3)
''',

    "concept": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark blue gradient background for better visibility
        bg = Rectangle(width=16, height=10, fill_color="#16213e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title with drawing effect
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(DrawBorderThenFill(title), run_time=1.0)
        self.wait(0.3)

        # Central concept with glow effect
        concept_box = RoundedRectangle(
            corner_radius=0.3, width=9, height=2.2,
            color=GREEN, fill_opacity=0.15, stroke_width=3
        ).move_to(ORIGIN + UP * 0.3)

        # Add subtle glow
        glow = concept_box.copy().set_stroke(GREEN, width=8, opacity=0.3)

        concept_text = Text("{main_concept}", font_size=34, color=GREEN, weight=BOLD)
        concept_text.move_to(concept_box.get_center())

        self.play(
            FadeIn(glow, scale=1.1),
            DrawBorderThenFill(concept_box),
            run_time=0.8
        )
        self.play(
            Write(concept_text),
            Circumscribe(concept_box, color=YELLOW, time_width=2),
            run_time=1.0
        )
        self.wait(0.5)

        # Supporting details with icons
        details = VGroup(
{detail_points_code}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(concept_box, DOWN, buff=0.6)

        # Animated entry with stagger
        self.play(
            LaggedStart(*[
                FadeIn(d, shift=LEFT * 0.3) for d in details
            ], lag_ratio=0.15),
            run_time=1.2
        )
        self.wait(2)

        # Highlight key concept and hold
        self.play(Indicate(concept_text, color=YELLOW, scale_factor=1.1))
        # Hold final frame for freeze (no fade out)
        self.wait(3)
''',

    "comparison": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background for better visibility
        bg = Rectangle(width=16, height=10, fill_color="#0f0f23", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title with emphasis
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)
        self.wait(0.3)

        # Left side with gradient border effect
        left_box = RoundedRectangle(
            corner_radius=0.2, width=5, height=3.5,
            color=RED_C, fill_opacity=0.1, stroke_width=3
        )
        left_header = Text("{left_label}", font_size=28, color=RED_C, weight=BOLD)
        left_underline = Line(LEFT * 1.5, RIGHT * 1.5, color=RED_C, stroke_width=2)
        left_items = VGroup(
{left_items_code}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)

        left_content = VGroup(left_header, left_underline, left_items).arrange(DOWN, buff=0.2)
        left_grp = VGroup(left_box, left_content).move_to(LEFT * 3 + DOWN * 0.2)
        left_content.move_to(left_box.get_center())

        # Right side
        right_box = RoundedRectangle(
            corner_radius=0.2, width=5, height=3.5,
            color=GREEN_C, fill_opacity=0.1, stroke_width=3
        )
        right_header = Text("{right_label}", font_size=28, color=GREEN_C, weight=BOLD)
        right_underline = Line(LEFT * 1.5, RIGHT * 1.5, color=GREEN_C, stroke_width=2)
        right_items = VGroup(
{right_items_code}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)

        right_content = VGroup(right_header, right_underline, right_items).arrange(DOWN, buff=0.2)
        right_grp = VGroup(right_box, right_content).move_to(RIGHT * 3 + DOWN * 0.2)
        right_content.move_to(right_box.get_center())

        # VS badge with circle
        vs_circle = Circle(radius=0.5, color=YELLOW, fill_opacity=0.9)
        vs_text = Text("VS", font_size=28, color=BLACK, weight=BOLD)
        vs = VGroup(vs_circle, vs_text).move_to(DOWN * 0.2)

        # Animated entry - slide in from sides
        self.play(
            FadeIn(left_grp, shift=RIGHT * 2),
            run_time=0.7
        )
        self.play(
            SpinInFromNothing(vs),
            run_time=0.5
        )
        self.play(
            FadeIn(right_grp, shift=LEFT * 2),
            run_time=0.7
        )
        self.wait(0.5)

        # Highlight each side
        self.play(Indicate(left_box, color=RED, scale_factor=1.02))
        self.wait(0.3)
        self.play(Indicate(right_box, color=GREEN, scale_factor=1.02))
        # Hold final frame for freeze (no fade out)
        self.wait(3)
''',

    "process": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background for better visibility
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title with animation
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(DrawBorderThenFill(title), run_time=0.8)
        self.wait(0.3)

        # Process steps with enhanced styling
        step_data = {step_data}
        colors = [BLUE_D, GREEN_D, ORANGE, PURPLE_B, TEAL_D]

        steps = VGroup()
        step_numbers = VGroup()

        for i, (step_title, step_desc) in enumerate(step_data):
            color = colors[i % len(colors)]

            # Step box with gradient feel
            box = RoundedRectangle(
                corner_radius=0.2, width=2.4, height=1.4,
                color=color, fill_opacity=0.2, stroke_width=3
            )

            # Step number badge
            num_circle = Circle(radius=0.25, color=color, fill_opacity=1)
            num_text = Text(str(i + 1), font_size=20, color=WHITE, weight=BOLD)
            num_badge = VGroup(num_circle, num_text)

            # Step title
            txt = Text(step_title, font_size=16, color=WHITE, weight=BOLD)
            txt.move_to(box.get_center())

            step_group = VGroup(box, txt)
            steps.add(step_group)
            step_numbers.add(num_badge)

        steps.arrange(RIGHT, buff=0.5).move_to(ORIGIN + DOWN * 0.1)

        # Position number badges above boxes
        for i, (step, badge) in enumerate(zip(steps, step_numbers)):
            badge.next_to(step, UP, buff=0.15)

        # Animate steps appearing one by one
        for i, (step, badge) in enumerate(zip(steps, step_numbers)):
            self.play(
                GrowFromCenter(badge),
                DrawBorderThenFill(step[0]),
                FadeIn(step[1]),
                run_time=0.5
            )
            self.wait(0.2)

        # Animated arrows with pulse effect
        arrows = VGroup()
        for i in range(len(steps) - 1):
            arr = Arrow(
                steps[i].get_right() + RIGHT * 0.1,
                steps[i + 1].get_left() + LEFT * 0.1,
                buff=0.05, color=YELLOW, stroke_width=4,
                max_tip_length_to_length_ratio=0.3
            )
            arrows.add(arr)

        self.play(
            LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2),
            run_time=0.8
        )
        self.wait(0.5)

        # Flash through the process
        for i, step in enumerate(steps):
            self.play(
                Flash(step, color=colors[i % len(colors)], line_length=0.3),
                run_time=0.3
            )

        # Hold final frame for freeze (no fade out)
        self.wait(3)
''',

    "example": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background for better visibility
        bg = Rectangle(width=16, height=10, fill_color="#0d1117", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)
        self.wait(0.3)

        # Example header with icon
        example_icon = Triangle(color=YELLOW, fill_opacity=1).scale(0.2)
        example_label = Text("EXAMPLE", font_size=24, color=YELLOW, weight=BOLD)
        example_header = VGroup(example_icon, example_label).arrange(RIGHT, buff=0.2)
        example_header.to_edge(LEFT, buff=0.8).shift(UP * 1.2)
        self.play(
            SpinInFromNothing(example_icon),
            FadeIn(example_label, shift=RIGHT * 0.3),
            run_time=0.6
        )

        # Code-style box with terminal look
        code_box = RoundedRectangle(
            corner_radius=0.15, width=11, height=3,
            color=GREY_D, fill_opacity=0.95, stroke_width=2
        ).move_to(ORIGIN + DOWN * 0.2)

        # Terminal header bar
        header_bar = Rectangle(
            width=11, height=0.4,
            color=GREY_B, fill_opacity=1
        ).next_to(code_box, UP, buff=0)

        # Terminal dots
        dots = VGroup(
            Dot(color=RED, radius=0.08),
            Dot(color=YELLOW, radius=0.08),
            Dot(color=GREEN, radius=0.08)
        ).arrange(RIGHT, buff=0.12).move_to(header_bar.get_left() + RIGHT * 0.5)

        terminal = VGroup(header_bar, dots, code_box)

        self.play(
            FadeIn(terminal, shift=UP * 0.3),
            run_time=0.6
        )

        # Example text with typewriter effect simulation
        example_text = Text(
            "{example_content}",
            font_size=24, color=GREEN_A, font="Monospace"
        ).move_to(code_box.get_center())

        self.play(Write(example_text), run_time=1.2)
        self.wait(0.5)

        # Cursor blink effect
        cursor = Line(UP * 0.2, DOWN * 0.2, color=WHITE, stroke_width=3)
        cursor.next_to(example_text, RIGHT, buff=0.1)
        self.play(FadeIn(cursor), run_time=0.1)
        self.play(FadeOut(cursor), run_time=0.2)
        self.play(FadeIn(cursor), run_time=0.1)
        self.play(FadeOut(cursor), run_time=0.2)

        # Result with success animation
        result_box = RoundedRectangle(
            corner_radius=0.1, width=8, height=0.8,
            color=GREEN, fill_opacity=0.2, stroke_width=2
        ).next_to(code_box, DOWN, buff=0.4)

        checkmark = Text("✓", font_size=28, color=GREEN)
        result_text = Text("{result_text}", font_size=22, color=GREEN_B, weight=BOLD)
        result_content = VGroup(checkmark, result_text).arrange(RIGHT, buff=0.2)
        result_content.move_to(result_box.get_center())

        self.play(
            DrawBorderThenFill(result_box),
            run_time=0.4
        )
        self.play(
            GrowFromCenter(checkmark),
            Write(result_text),
            Flash(result_box, color=GREEN, line_length=0.2),
            run_time=0.6
        )
        # Hold final frame for freeze (no fade out)
        self.wait(3)
''',

    "conclusion": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark gradient background for better visibility
        bg = Rectangle(width=16, height=10, fill_color="#16213e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title with celebratory entry
        title = Text("{title}", font_size=44, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(
            GrowFromCenter(title),
            Flash(title, color=BLUE, line_length=0.4, num_lines=12),
            run_time=1.0
        )
        self.wait(0.3)

        # Key takeaways header
        takeaway_header = Text("Key Takeaways", font_size=28, color=YELLOW)
        takeaway_header.next_to(title, DOWN, buff=0.5)
        header_line = Line(LEFT * 2, RIGHT * 2, color=YELLOW, stroke_width=2)
        header_line.next_to(takeaway_header, DOWN, buff=0.1)

        self.play(
            FadeIn(takeaway_header, shift=DOWN * 0.2),
            Create(header_line),
            run_time=0.5
        )

        # Key takeaways with checkmarks
        takeaways = VGroup(
{takeaway_points_code}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).next_to(header_line, DOWN, buff=0.5)

        # Add checkmark icons
        for i, t in enumerate(takeaways):
            check = Text("✓", font_size=26, color=GREEN).next_to(t, LEFT, buff=0.2)
            self.play(
                GrowFromCenter(check),
                FadeIn(t, shift=RIGHT * 0.3),
                run_time=0.4
            )
            self.wait(0.15)

        self.wait(0.8)

        # Final message with dramatic reveal
        finale_box = RoundedRectangle(
            corner_radius=0.2, width=10, height=1.2,
            color=GOLD, fill_opacity=0.15, stroke_width=3
        ).to_edge(DOWN, buff=0.6)

        finale = Text(
            "{final_message}",
            font_size=30, color=GOLD, weight=BOLD
        ).move_to(finale_box.get_center())

        # Stars decoration
        stars = VGroup(*[
            Star(n=5, color=YELLOW, fill_opacity=0.8).scale(0.15)
            for _ in range(6)
        ])
        stars.arrange(RIGHT, buff=0.4).next_to(finale_box, UP, buff=0.15)

        self.play(
            DrawBorderThenFill(finale_box),
            run_time=0.5
        )
        self.play(
            Write(finale),
            LaggedStart(*[
                SpinInFromNothing(star) for star in stars
            ], lag_ratio=0.1),
            run_time=1.0
        )

        # Celebration flash
        self.play(
            Circumscribe(finale, color=YELLOW, time_width=1.5),
            run_time=0.8
        )
        # Hold final frame for freeze (no fade out)
        self.wait(3)
''',

    # ═══════════════════════════════════════════════════════════════════════════
    # ADVANCED TEMPLATES - Rich Manim Features
    # ═══════════════════════════════════════════════════════════════════════════

    "data_chart": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Animated bar chart
        values = {chart_values}
        labels = {chart_labels}
        colors = [BLUE_D, GREEN_D, ORANGE, PURPLE_B, RED_D, TEAL_D]

        max_val = max(values) if values else 1
        bars = VGroup()
        bar_labels = VGroup()
        value_texts = VGroup()

        for i, (val, label) in enumerate(zip(values, labels)):
            # Animated bar with gradient effect
            bar_height = (val / max_val) * 2.8
            bar = Rectangle(
                width=0.8, height=bar_height,
                fill_color=colors[i % len(colors)],
                fill_opacity=0.85,
                stroke_color=WHITE,
                stroke_width=1
            )
            bar.move_to(ORIGIN + LEFT * 3.5 + RIGHT * i * 1.2)
            bar.align_to(ORIGIN + DOWN * 1.5, DOWN)

            # Label below
            lbl = Text(str(label)[:8], font_size=16, color=WHITE)
            lbl.next_to(bar, DOWN, buff=0.15)

            # Value on top
            val_txt = Text(str(val), font_size=18, color=colors[i % len(colors)], weight=BOLD)
            val_txt.next_to(bar, UP, buff=0.1)

            bars.add(bar)
            bar_labels.add(lbl)
            value_texts.add(val_txt)

        # Scale to fit
        chart_group = VGroup(bars, bar_labels, value_texts)
        if chart_group.get_width() > 11:
            chart_group.scale_to_fit_width(10.5)
        chart_group.move_to(ORIGIN + DOWN * 0.3)

        # Animate bars growing from bottom
        for i, (bar, lbl, val) in enumerate(zip(bars, bar_labels, value_texts)):
            target_height = bar.height
            bar.stretch_to_fit_height(0.01)
            bar.align_to(ORIGIN + DOWN * 1.5, DOWN)
            self.play(
                bar.animate.stretch_to_fit_height(target_height).align_to(ORIGIN + DOWN * 1.5, DOWN),
                FadeIn(lbl),
                run_time=0.4
            )
            self.play(FadeIn(val, shift=DOWN * 0.2), run_time=0.2)

        # Highlight max value
        max_idx = values.index(max(values))
        self.play(
            Flash(bars[max_idx], color=YELLOW, line_length=0.3),
            Indicate(value_texts[max_idx], color=YELLOW, scale_factor=1.3),
            run_time=0.6
        )
        self.wait(3)
''',

    "math_formula": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#0f0f23", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Main equation with animated writing
        equation = MathTex(r"{equation}", font_size=48, color=WHITE)
        equation.move_to(ORIGIN + UP * 0.8)

        # Box around equation
        eq_box = SurroundingRectangle(
            equation, color=BLUE, buff=0.3,
            corner_radius=0.1, stroke_width=2
        )

        self.play(Write(equation), run_time=1.5)
        self.play(Create(eq_box), run_time=0.5)
        self.wait(0.5)

        # Explanation text
        explanation = Text("{explanation}", font_size=24, color=GREY_B)
        explanation.next_to(eq_box, DOWN, buff=0.6)

        # Scale if needed
        if explanation.get_width() > 11:
            explanation.scale_to_fit_width(10.5)

        self.play(FadeIn(explanation, shift=UP * 0.3), run_time=0.6)

        # Highlight parts of the equation
        self.play(Circumscribe(equation, color=YELLOW, time_width=2), run_time=1.0)
        self.wait(3)
''',

    "equation_derivation": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background optimized for math
        bg = Rectangle(width=16, height=10, fill_color="#0f0f1a", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=36, color="#7aa2f7", weight=BOLD)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=0.6)

        # Derivation steps - each step transforms into the next
        steps = {derivation_steps}

        # Color mapping for consistent variable highlighting
        color_map = {{
            "x": BLUE,
            "y": GREEN,
            "a": ORANGE,
            "b": YELLOW,
            "c": PURPLE,
            "=": WHITE,
        }}

        prev_eq = None
        step_group = VGroup()

        for i, (step_label, latex_eq) in enumerate(steps):
            # Step number
            step_num = Text(f"Step {{i+1}}:", font_size=20, color=GREY_B)

            # Equation with color mapping
            equation = MathTex(latex_eq, font_size=36, tex_to_color_map=color_map)

            # Group step label and equation
            step_row = VGroup(step_num, equation).arrange(RIGHT, buff=0.5)
            step_group.add(step_row)

        # Arrange all steps vertically
        step_group.arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        step_group.next_to(title, DOWN, buff=0.6)

        # Scale to fit if needed
        if step_group.get_width() > 12:
            step_group.scale_to_fit_width(11.5)
        if step_group.get_height() > 5.5:
            step_group.scale_to_fit_height(5)

        # Animate each step with transformation effect
        for i, step_row in enumerate(step_group):
            if i == 0:
                self.play(Write(step_row), run_time=1.0)
            else:
                # Show step label
                self.play(FadeIn(step_row[0]), run_time=0.3)
                # Transform from previous equation to current
                if i > 0:
                    prev_eq = step_group[i-1][1].copy()
                    self.play(
                        TransformMatchingTex(prev_eq, step_row[1]),
                        run_time=1.2
                    )
            self.wait(0.6)

        # Final highlight on the result
        final_eq = step_group[-1][1]
        result_box = SurroundingRectangle(
            final_eq, color="#e0af68", buff=0.15,
            corner_radius=0.1, stroke_width=2
        )
        self.play(Create(result_box), run_time=0.5)

        # Result label
        result_label = Text("Result", font_size=18, color="#e0af68")
        result_label.next_to(result_box, RIGHT, buff=0.3)
        self.play(FadeIn(result_label), run_time=0.3)

        self.wait(3)
''',

    "graph_visualization": '''from manim import *
import numpy as np

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#0f0f1a", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=36, color="#7aa2f7", weight=BOLD)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=0.6)

        # Create axes
        axes = Axes(
            x_range={x_range},
            y_range={y_range},
            x_length=8,
            y_length=5,
            axis_config={{
                "color": GREY_B,
                "stroke_width": 2,
                "include_numbers": True,
                "font_size": 20,
            }},
            tips=True,
        )
        axes.shift(DOWN * 0.3)

        # Axis labels
        x_label = MathTex("{x_label}", font_size=24, color=WHITE)
        x_label.next_to(axes.x_axis, RIGHT, buff=0.2)
        y_label = MathTex("{y_label}", font_size=24, color=WHITE)
        y_label.next_to(axes.y_axis, UP, buff=0.2)

        self.play(Create(axes), run_time=1.0)
        self.play(Write(x_label), Write(y_label), run_time=0.4)

        # Function equation display
        func_eq = MathTex(r"{function_latex}", font_size=32, color=WHITE)
        func_eq.to_corner(UR, buff=0.5)
        eq_box = SurroundingRectangle(func_eq, color=BLUE, buff=0.15, corner_radius=0.1)

        self.play(Write(func_eq), Create(eq_box), run_time=0.6)

        # Plot the function
        graph = axes.plot(
            lambda x: {function_code},
            color=BLUE,
            stroke_width=3,
        )

        self.play(Create(graph), run_time=1.5)

        # Key points (roots, vertex, etc.)
        key_points = {key_points}

        for point_data in key_points:
            x, y, label = point_data[0], point_data[1], point_data[2]
            dot = Dot(axes.c2p(x, y), color=YELLOW, radius=0.1)
            dot_label = MathTex(label, font_size=20, color=YELLOW)
            dot_label.next_to(dot, UR, buff=0.15)

            self.play(
                GrowFromCenter(dot),
                Write(dot_label),
                run_time=0.5
            )

        self.wait(3)
''',

    "geometric_theorem": '''from manim import *
import numpy as np

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#0f0f1a", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=36, color="#7aa2f7", weight=BOLD)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=0.6)

        # Theorem statement
        theorem = MathTex(r"{theorem_latex}", font_size=40, color=WHITE)
        theorem.next_to(title, DOWN, buff=0.5)
        self.play(Write(theorem), run_time=1.0)
        self.wait(0.5)

        # Create the geometric shape
        shape_type = "{shape_type}"
        shape_group = VGroup()

        if shape_type == "triangle":
            # Right triangle for Pythagorean theorem
            vertices = {vertices}
            triangle = Polygon(*[np.array(v) for v in vertices], color=BLUE, fill_opacity=0.3, stroke_width=3)
            shape_group.add(triangle)

            # Side labels
            labels = {side_labels}
            for label_data in labels:
                pos = np.array(label_data[0])
                text = label_data[1]
                label = MathTex(text, font_size=28, color=YELLOW)
                label.move_to(pos)
                shape_group.add(label)

            # Right angle marker if applicable
            shape_group.add(
                Square(side_length=0.3, color=WHITE, stroke_width=2)
                .move_to(np.array(vertices[1]) + np.array([0.15, 0.15, 0]))
            )

        elif shape_type == "circle":
            circle = Circle(radius=1.5, color=BLUE, stroke_width=3)
            shape_group.add(circle)

        elif shape_type == "polygon":
            vertices = {vertices}
            polygon = Polygon(*[np.array(v) for v in vertices], color=BLUE, fill_opacity=0.3, stroke_width=3)
            shape_group.add(polygon)

        # Position shape
        shape_group.move_to(DOWN * 0.8 + LEFT * 2)

        self.play(Create(shape_group), run_time=1.5)

        # Proof steps or explanations
        proof_steps = {proof_steps}
        proof_group = VGroup()

        for step in proof_steps:
            step_text = MathTex(step, font_size=24, color=WHITE)
            proof_group.add(step_text)

        proof_group.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        proof_group.move_to(DOWN * 0.8 + RIGHT * 2.5)

        for step_text in proof_group:
            self.play(Write(step_text), run_time=0.8)
            self.wait(0.3)

        # QED or conclusion highlight
        qed = Text("∎", font_size=36, color="#9ece6a")
        qed.next_to(proof_group, DOWN, buff=0.3)
        self.play(FadeIn(qed, scale=1.5), run_time=0.5)

        self.wait(3)
''',

    "matrix_operation": '''from manim import *
import numpy as np

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#0f0f1a", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=36, color="#7aa2f7", weight=BOLD)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=0.6)

        # Matrix A
        matrix_a_data = {matrix_a}
        matrix_a = Matrix(
            matrix_a_data,
            left_bracket="[",
            right_bracket="]",
            element_to_mobject_config={{"font_size": 32}}
        )
        matrix_a.set_color(BLUE)

        # Operation symbol
        operation = "{operation}"
        if operation == "multiply":
            op_symbol = MathTex(r"\\times", font_size=40, color=WHITE)
        elif operation == "add":
            op_symbol = MathTex(r"+", font_size=40, color=WHITE)
        elif operation == "determinant":
            op_symbol = MathTex(r"\\det", font_size=32, color=WHITE)
        else:
            op_symbol = MathTex(r"=", font_size=40, color=WHITE)

        # Matrix B (if applicable)
        matrix_b_data = {matrix_b}
        if matrix_b_data:
            matrix_b = Matrix(
                matrix_b_data,
                left_bracket="[",
                right_bracket="]",
                element_to_mobject_config={{"font_size": 32}}
            )
            matrix_b.set_color(GREEN)

            equals = MathTex(r"=", font_size=40, color=WHITE)

            # Result matrix
            result_data = {result_matrix}
            result_matrix = Matrix(
                result_data,
                left_bracket="[",
                right_bracket="]",
                element_to_mobject_config={{"font_size": 32}}
            )
            result_matrix.set_color(YELLOW)

            # Arrange matrices
            equation = VGroup(matrix_a, op_symbol, matrix_b, equals, result_matrix)
            equation.arrange(RIGHT, buff=0.4)
        else:
            equals = MathTex(r"=", font_size=40, color=WHITE)
            result_val = MathTex(r"{scalar_result}", font_size=40, color=YELLOW)
            equation = VGroup(op_symbol, matrix_a, equals, result_val)
            equation.arrange(RIGHT, buff=0.3)

        equation.move_to(ORIGIN)

        # Scale if needed
        if equation.get_width() > 12:
            equation.scale_to_fit_width(11.5)

        # Animate matrix appearance
        self.play(Write(matrix_a), run_time=1.0)
        self.play(Write(op_symbol), run_time=0.3)

        if matrix_b_data:
            self.play(Write(matrix_b), run_time=1.0)
            self.play(Write(equals), run_time=0.3)

            # Highlight row-column multiplication
            for i in range(len(matrix_a_data)):
                row = VGroup(*matrix_a.get_rows()[i])
                col = VGroup(*matrix_b.get_columns()[min(i, len(matrix_b_data[0])-1)])
                self.play(
                    row.animate.set_color(YELLOW),
                    col.animate.set_color(YELLOW),
                    run_time=0.3
                )
                self.play(
                    row.animate.set_color(BLUE),
                    col.animate.set_color(GREEN),
                    run_time=0.2
                )

            self.play(Write(result_matrix), run_time=1.0)
        else:
            self.play(Write(equals), Write(result_val), run_time=0.5)

        # Final highlight
        self.play(
            Circumscribe(equation, color="#e0af68", time_width=2),
            run_time=1.0
        )

        self.wait(3)
''',

    "timeline": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Timeline line
        timeline = Line(LEFT * 5.5, RIGHT * 5.5, color=WHITE, stroke_width=3)
        timeline.move_to(ORIGIN)

        self.play(Create(timeline), run_time=0.8)

        # Timeline events
        events = {timeline_events}
        colors = [BLUE_D, GREEN_D, ORANGE, PURPLE_B, TEAL_D]
        n_events = len(events)

        dots = VGroup()
        labels = VGroup()
        connectors = VGroup()

        for i, (year, event) in enumerate(events):
            x_pos = -5 + (i * 10 / max(n_events - 1, 1))
            color = colors[i % len(colors)]

            # Pulsing dot
            dot = Dot(point=[x_pos, 0, 0], radius=0.15, color=color)
            dot_glow = Dot(point=[x_pos, 0, 0], radius=0.25, color=color, fill_opacity=0.3)

            # Year label
            year_label = Text(str(year)[:10], font_size=16, color=color, weight=BOLD)
            year_label.next_to(dot, UP, buff=0.2)

            # Event label (alternating top/bottom)
            event_label = Text(str(event)[:20], font_size=14, color=WHITE)
            if i % 2 == 0:
                event_label.next_to(year_label, UP, buff=0.15)
            else:
                event_label.next_to(dot, DOWN, buff=0.35)

            dots.add(VGroup(dot_glow, dot))
            labels.add(VGroup(year_label, event_label))

        # Animate timeline events appearing
        for i, (dot_grp, label_grp) in enumerate(zip(dots, labels)):
            self.play(
                GrowFromCenter(dot_grp),
                FadeIn(label_grp, shift=DOWN * 0.2 if i % 2 == 0 else UP * 0.2),
                run_time=0.5
            )
            self.wait(0.2)

        # Progress line sweep
        progress = Line(LEFT * 5.5, LEFT * 5.5, color=YELLOW, stroke_width=5)
        progress.move_to(timeline)
        self.play(progress.animate.put_start_and_end_on(LEFT * 5.5, RIGHT * 5.5), run_time=1.5)

        self.wait(3)
''',

    "diagram": '''from manim import *
import numpy as np

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#16213e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Central node
        center_text = Text("{center_node}", font_size=24, color=WHITE, weight=BOLD)
        center_circle = Circle(radius=0.8, color=BLUE, fill_opacity=0.3, stroke_width=3)
        center_node = VGroup(center_circle, center_text)
        center_node.move_to(ORIGIN)

        self.play(GrowFromCenter(center_node), run_time=0.7)

        # Connected nodes
        nodes_data = {connected_nodes}
        colors = [GREEN_D, ORANGE, PURPLE_B, RED_D, TEAL_D, YELLOW_D]
        n_nodes = len(nodes_data)

        nodes = VGroup()
        arrows = VGroup()

        for i, node_text in enumerate(nodes_data):
            angle = i * TAU / n_nodes - PI/2  # Start from top
            radius = 2.2
            pos = center_node.get_center() + radius * np.array([np.cos(angle), np.sin(angle), 0])
            color = colors[i % len(colors)]

            # Node
            node_label = Text(str(node_text)[:15], font_size=18, color=WHITE)
            node_box = RoundedRectangle(
                corner_radius=0.1,
                width=node_label.get_width() + 0.4,
                height=0.6,
                color=color, fill_opacity=0.2, stroke_width=2
            )
            node = VGroup(node_box, node_label).move_to(pos)
            nodes.add(node)

            # Curved arrow from center to node
            arrow = CurvedArrow(
                center_circle.get_edge_center(pos - center_node.get_center()),
                node_box.get_edge_center(center_node.get_center() - pos),
                color=color, stroke_width=2,
                angle=0.3 if i % 2 == 0 else -0.3
            )
            arrows.add(arrow)

        # Scale to fit
        all_elements = VGroup(center_node, nodes, arrows)
        if all_elements.get_width() > 11:
            all_elements.scale_to_fit_width(10.5)
        all_elements.move_to(ORIGIN + DOWN * 0.3)

        # Animate connections
        for node, arrow in zip(nodes, arrows):
            self.play(
                GrowArrow(arrow),
                FadeIn(node, scale=0.5),
                run_time=0.4
            )
            self.wait(0.1)

        # Pulse center
        self.play(
            Indicate(center_node, color=YELLOW, scale_factor=1.1),
            run_time=0.6
        )
        self.wait(3)
''',

    "metrics": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Metrics data
        metrics = {metrics_data}
        colors = [BLUE_D, GREEN_D, ORANGE, PURPLE_B]

        metric_groups = VGroup()

        for i, (label, value, unit) in enumerate(metrics[:4]):
            color = colors[i % len(colors)]

            # Value tracker for animation
            tracker = ValueTracker(0)

            # Create decimal number
            number = DecimalNumber(
                0, num_decimal_places=0,
                font_size=48, color=color
            )
            number.add_updater(lambda m, t=tracker: m.set_value(t.get_value()))

            # Unit label
            unit_text = Text(str(unit)[:8], font_size=20, color=GREY_B)
            unit_text.next_to(number, RIGHT, buff=0.15)

            # Metric label
            label_text = Text(str(label)[:15], font_size=22, color=WHITE, weight=BOLD)

            # Group
            metric_grp = VGroup(number, unit_text, label_text)
            label_text.next_to(VGroup(number, unit_text), DOWN, buff=0.2)
            metric_groups.add(VGroup(metric_grp, tracker, value))

        # Arrange metrics in 2x2 grid
        positions = [UP * 0.8 + LEFT * 3, UP * 0.8 + RIGHT * 3,
                     DOWN * 1.2 + LEFT * 3, DOWN * 1.2 + RIGHT * 3]

        for mg, pos in zip(metric_groups, positions):
            mg[0].move_to(pos)

        # Add all metric displays
        for mg in metric_groups:
            self.add(mg[0])

        # Animate all counters simultaneously
        self.play(*[
            mg[1].animate.set_value(int(mg[2]))
            for mg in metric_groups
        ], run_time=2.0, rate_func=smooth)

        # Remove updaters and highlight
        for i, mg in enumerate(metric_groups):
            mg[0][0].clear_updaters()
            self.play(
                Flash(mg[0][0], color=colors[i], line_length=0.2),
                run_time=0.3
            )

        self.wait(3)
''',

    "hierarchy": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#0f0f23", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Hierarchy data: [root, [child1, child2, ...]]
        root_label = "{root_node}"
        children = {child_nodes}

        # Root node at top
        root_text = Text(root_label[:20], font_size=24, color=WHITE, weight=BOLD)
        root_box = RoundedRectangle(
            corner_radius=0.15,
            width=root_text.get_width() + 0.6,
            height=0.8,
            color=BLUE, fill_opacity=0.3, stroke_width=3
        )
        root = VGroup(root_box, root_text).move_to(UP * 1.8)

        self.play(GrowFromCenter(root), run_time=0.6)

        # Child nodes
        n_children = min(len(children), 5)
        child_nodes_grp = VGroup()
        arrows = VGroup()

        total_width = (n_children - 1) * 2.5
        start_x = -total_width / 2

        for i, child_label in enumerate(children[:n_children]):
            x_pos = start_x + i * 2.5
            color = [GREEN_D, ORANGE, PURPLE_B, RED_D, TEAL_D][i % 5]

            child_text = Text(str(child_label)[:12], font_size=18, color=WHITE)
            child_box = RoundedRectangle(
                corner_radius=0.1,
                width=max(child_text.get_width() + 0.4, 1.5),
                height=0.6,
                color=color, fill_opacity=0.2, stroke_width=2
            )
            child = VGroup(child_box, child_text).move_to([x_pos, -0.5, 0])
            child_nodes_grp.add(child)

            # Arrow from root to child
            arrow = Arrow(
                root_box.get_bottom(),
                child_box.get_top(),
                color=GREY_B, stroke_width=2,
                buff=0.1
            )
            arrows.add(arrow)

        # Scale to fit
        all_elements = VGroup(root, child_nodes_grp, arrows)
        if all_elements.get_width() > 11:
            all_elements.scale_to_fit_width(10.5)
        all_elements.move_to(ORIGIN + DOWN * 0.3)

        # Animate children appearing
        for arrow, child in zip(arrows, child_nodes_grp):
            self.play(
                GrowArrow(arrow),
                FadeIn(child, shift=UP * 0.3),
                run_time=0.4
            )

        # Highlight root
        self.play(Indicate(root, color=YELLOW, scale_factor=1.05), run_time=0.5)
        self.wait(3)
''',

    # ═══════════════════════════════════════════════════════════════════════════
    # CLAUDE-STYLE VISUAL EXPLANATION TEMPLATES
    # Clean, professional layouts inspired by Claude's visual explanations
    # ═══════════════════════════════════════════════════════════════════════════

    "visual_explanation": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # ═══ CLAUDE-STYLE COLORS ═══
        BG_DARK = "#1a1b26"
        BG_CARD = "#24283b"
        OPTION_A_COLOR = "#364fc7"
        OPTION_A_LIGHT = "#4263eb"
        OPTION_B_COLOR = "#2f9e44"
        OPTION_B_LIGHT = "#40c057"
        RECOMMEND_COLOR = "#0ca678"
        TEXT_PRIMARY = "#c0caf5"
        TEXT_HEADING = "#7aa2f7"
        BORDER_SUBTLE = "#3b4261"

        # Background
        bg = Rectangle(width=16, height=10, fill_color=BG_DARK, fill_opacity=1, stroke_width=0)
        self.add(bg)

        # ═══ HEADER BOX ═══
        header_box = RoundedRectangle(
            corner_radius=0.15, width=12.5, height=0.9,
            fill_color=BG_CARD, fill_opacity=1,
            stroke_color=BORDER_SUBTLE, stroke_width=1
        ).to_edge(UP, buff=0.4)

        title = Text("{title}", font_size=32, color=TEXT_HEADING, weight=BOLD)
        title.move_to(header_box.get_center())

        self.play(FadeIn(header_box), Write(title), run_time=0.8)
        self.wait(0.3)

        # ═══ TWO-COLUMN COMPARISON ═══
        # Option A (Left)
        option_a_header = RoundedRectangle(
            corner_radius=0.1, width=5.5, height=0.6,
            fill_color=OPTION_A_COLOR, fill_opacity=1, stroke_width=0
        )
        option_a_label = Text("{option_a_label}", font_size=22, color=WHITE, weight=BOLD)
        option_a_label.move_to(option_a_header.get_center())
        option_a_top = VGroup(option_a_header, option_a_label)

        option_a_body = RoundedRectangle(
            corner_radius=0.1, width=5.5, height=2.8,
            fill_color=BG_CARD, fill_opacity=1,
            stroke_color=OPTION_A_COLOR, stroke_width=2
        )

        option_a_points = VGroup(
{option_a_points_code}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        option_a_points.move_to(option_a_body.get_center())
        if option_a_points.get_width() > 5:
            option_a_points.scale_to_fit_width(4.8)

        option_a_card = VGroup(option_a_top, option_a_body, option_a_points)
        option_a_body.next_to(option_a_top, DOWN, buff=0)
        option_a_points.move_to(option_a_body.get_center())
        option_a_card.move_to(LEFT * 3.2 + DOWN * 0.3)

        # Option B (Right)
        option_b_header = RoundedRectangle(
            corner_radius=0.1, width=5.5, height=0.6,
            fill_color=OPTION_B_COLOR, fill_opacity=1, stroke_width=0
        )
        option_b_label = Text("{option_b_label}", font_size=22, color=WHITE, weight=BOLD)
        option_b_label.move_to(option_b_header.get_center())
        option_b_top = VGroup(option_b_header, option_b_label)

        option_b_body = RoundedRectangle(
            corner_radius=0.1, width=5.5, height=2.8,
            fill_color=BG_CARD, fill_opacity=1,
            stroke_color=OPTION_B_COLOR, stroke_width=2
        )

        option_b_points = VGroup(
{option_b_points_code}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        option_b_points.move_to(option_b_body.get_center())
        if option_b_points.get_width() > 5:
            option_b_points.scale_to_fit_width(4.8)

        option_b_card = VGroup(option_b_top, option_b_body, option_b_points)
        option_b_body.next_to(option_b_top, DOWN, buff=0)
        option_b_points.move_to(option_b_body.get_center())
        option_b_card.move_to(RIGHT * 3.2 + DOWN * 0.3)

        # Animate cards
        self.play(FadeIn(option_a_card, shift=RIGHT * 0.5), run_time=0.6)
        self.play(FadeIn(option_b_card, shift=LEFT * 0.5), run_time=0.6)
        self.wait(0.4)

        # ═══ RECOMMENDATION BANNER ═══
        recommend_box = RoundedRectangle(
            corner_radius=0.15, width=11, height=0.7,
            fill_color=RECOMMEND_COLOR, fill_opacity=0.9, stroke_width=0
        ).to_edge(DOWN, buff=0.5)

        recommend_text = Text("{recommendation}", font_size=20, color=WHITE, weight=BOLD)
        recommend_text.move_to(recommend_box.get_center())
        if recommend_text.get_width() > 10.5:
            recommend_text.scale_to_fit_width(10)

        self.play(
            FadeIn(recommend_box, shift=UP * 0.3),
            Write(recommend_text),
            run_time=0.7
        )
        self.wait(3)
''',

    "info_card": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # ═══ CLAUDE-STYLE COLORS ═══
        BG_DARK = "#1a1b26"
        BG_CARD = "#24283b"
        TEXT_PRIMARY = "#c0caf5"
        TEXT_HEADING = "#7aa2f7"
        TEXT_SECONDARY = "#565f89"
        BORDER_SUBTLE = "#3b4261"
        ACCENT_BLUE = "#7dcfff"

        # Background
        bg = Rectangle(width=16, height=10, fill_color=BG_DARK, fill_opacity=1, stroke_width=0)
        self.add(bg)

        # ═══ TITLE ═══
        title = Text("{title}", font_size=36, color=TEXT_HEADING, weight=BOLD)
        title.to_edge(UP, buff=0.5)
        title_line = Line(LEFT * 5.5, RIGHT * 5.5, color=BORDER_SUBTLE, stroke_width=1)
        title_line.next_to(title, DOWN, buff=0.15)

        self.play(Write(title), Create(title_line), run_time=0.8)
        self.wait(0.3)

        # ═══ OVERVIEW SECTION ═══
        overview_label = Text("Overview", font_size=22, color=ACCENT_BLUE, weight=BOLD)
        overview_label.next_to(title_line, DOWN, buff=0.4).align_to(LEFT * 5.5, LEFT)

        overview_box = RoundedRectangle(
            corner_radius=0.1, width=11.5, height=1.4,
            fill_color=BG_CARD, fill_opacity=1,
            stroke_color=BORDER_SUBTLE, stroke_width=1
        )
        overview_box.next_to(overview_label, DOWN, buff=0.15)

        overview_text = Text("{overview_text}", font_size=20, color=TEXT_PRIMARY)
        overview_text.move_to(overview_box.get_center())
        if overview_text.get_width() > 11:
            overview_text.scale_to_fit_width(10.8)

        self.play(
            FadeIn(overview_label, shift=DOWN * 0.2),
            run_time=0.4
        )
        self.play(
            FadeIn(overview_box),
            Write(overview_text),
            run_time=0.6
        )
        self.wait(0.3)

        # ═══ KEY POINTS SECTION ═══
        points_label = Text("Key Points", font_size=22, color=ACCENT_BLUE, weight=BOLD)
        points_label.next_to(overview_box, DOWN, buff=0.4).align_to(LEFT * 5.5, LEFT)

        points_box = RoundedRectangle(
            corner_radius=0.1, width=11.5, height=2.2,
            fill_color=BG_CARD, fill_opacity=1,
            stroke_color=BORDER_SUBTLE, stroke_width=1
        )
        points_box.next_to(points_label, DOWN, buff=0.15)

        key_points = VGroup(
{key_points_code}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        key_points.move_to(points_box.get_center())
        if key_points.get_width() > 11:
            key_points.scale_to_fit_width(10.8)

        self.play(
            FadeIn(points_label, shift=DOWN * 0.2),
            run_time=0.4
        )
        self.play(FadeIn(points_box), run_time=0.3)

        # Animate points one by one
        for point in key_points:
            self.play(FadeIn(point, shift=RIGHT * 0.3), run_time=0.3)

        self.wait(3)
''',

    "decision_tree": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # ═══ CLAUDE-STYLE COLORS ═══
        BG_DARK = "#1a1b26"
        BG_CARD = "#24283b"
        TEXT_PRIMARY = "#c0caf5"
        TEXT_HEADING = "#7aa2f7"
        BORDER_SUBTLE = "#3b4261"
        STEP_COLORS = ["#7aa2f7", "#9ece6a", "#e0af68", "#bb9af7", "#7dcfff"]
        ARROW_COLOR = "#565f89"

        # Background
        bg = Rectangle(width=16, height=10, fill_color=BG_DARK, fill_opacity=1, stroke_width=0)
        self.add(bg)

        # ═══ TITLE ═══
        title = Text("{title}", font_size=36, color=TEXT_HEADING, weight=BOLD)
        title.to_edge(UP, buff=0.4)

        self.play(Write(title), run_time=0.7)
        self.wait(0.2)

        # ═══ DECISION FLOW STEPS ═══
        steps_data = {steps_data}
        n_steps = len(steps_data)

        step_boxes = VGroup()
        step_arrows = VGroup()

        # Calculate vertical spacing
        total_height = 5.5
        step_height = 0.8
        gap = (total_height - n_steps * step_height) / max(n_steps - 1, 1)

        for i, (step_title, step_desc) in enumerate(steps_data):
            color = STEP_COLORS[i % len(STEP_COLORS)]

            # Step number badge
            badge = Circle(radius=0.25, fill_color=color, fill_opacity=1, stroke_width=0)
            badge_num = Text(str(i + 1), font_size=18, color=BG_DARK, weight=BOLD)
            badge_num.move_to(badge.get_center())
            badge_grp = VGroup(badge, badge_num)

            # Step box
            box = RoundedRectangle(
                corner_radius=0.1, width=8, height=step_height,
                fill_color=BG_CARD, fill_opacity=1,
                stroke_color=color, stroke_width=2
            )

            # Step text
            step_txt = Text(step_title[:30], font_size=20, color=TEXT_PRIMARY, weight=BOLD)
            step_txt.move_to(box.get_center())
            if step_txt.get_width() > 7.5:
                step_txt.scale_to_fit_width(7)

            # Position
            y_pos = 2.2 - i * (step_height + gap)
            box.move_to([0, y_pos, 0])
            step_txt.move_to(box.get_center())
            badge_grp.next_to(box, LEFT, buff=0.3)

            step_group = VGroup(badge_grp, box, step_txt)
            step_boxes.add(step_group)

            # Arrow to next step
            if i < n_steps - 1:
                arrow = Arrow(
                    box.get_bottom() + DOWN * 0.1,
                    box.get_bottom() + DOWN * gap * 0.7,
                    color=ARROW_COLOR, stroke_width=3,
                    max_tip_length_to_length_ratio=0.4
                )
                step_arrows.add(arrow)

        # Animate steps appearing
        for i, step in enumerate(step_boxes):
            self.play(
                GrowFromCenter(step[0]),  # Badge
                FadeIn(step[1]),          # Box
                Write(step[2]),           # Text
                run_time=0.5
            )
            if i < len(step_arrows):
                self.play(GrowArrow(step_arrows[i]), run_time=0.3)

        self.wait(3)
'''
}


# ─── Parameter Extraction ───────────────────────────────────────────────────

def call_ollama_json(prompt: str, timeout: int = None, retry_on_fail: bool = False) -> dict:
    """
    Call Ollama and parse JSON response.

    Args:
        prompt: The prompt to send
        timeout: Custom timeout in seconds (default: PARAM_EXTRACTOR_TIMEOUT)
        retry_on_fail: If True, retry with extended timeout on failure

    Returns:
        Parsed JSON dict, or empty dict on failure
    """
    timeout = timeout or PARAM_EXTRACTOR_TIMEOUT

    def _make_request(current_timeout: int) -> dict:
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": PARAM_EXTRACTOR_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 500}
                },
                timeout=current_timeout
            )
            response.raise_for_status()
            text = response.json().get("response", "")

            # Extract JSON from response
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                json_str = match.group()
                # Fix common JSON issues
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)  # trailing commas
                json_str = json_str.replace("\n", " ")  # newlines
                return json.loads(json_str)
        except requests.exceptions.Timeout:
            print(f"  ⏱️  Param extraction timed out ({current_timeout}s)")
            return None
        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"  ⚠️  Param extraction error: {e}")
            return None
        return {}

    # First attempt
    result = _make_request(timeout)

    # Retry with extended timeout if enabled and first attempt failed
    if result is None and retry_on_fail:
        print(f"  🔄 Retrying with extended timeout ({PARAM_EXTRACTOR_RETRY_TIMEOUT}s)...")
        result = _make_request(PARAM_EXTRACTOR_RETRY_TIMEOUT)

    return result if result is not None else {}


def extract_intro_params(scene: dict) -> dict:
    """Extract parameters for intro template with content-aware fallback."""
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', '')
    narration = scene.get('narration_text', '')

    prompt = f"""Extract parameters for an intro animation from this scene.

Title: {title}
Visual Description: {scene.get('visual_description', '')}
Narration: {narration}

Return JSON with SPECIFIC content from the narration:
- subtitle: 1-line subtitle (10 words max) - summarize the main topic
- bullet_points: array of 3-4 key points (8 words each max) - extract actual points mentioned

DO NOT use generic "Point 1", "Point 2" - use actual content.

JSON:"""

    params = call_ollama_json(prompt, retry_on_fail=True)

    # Extract with validation
    subtitle = params.get("subtitle", "")
    points = params.get("bullet_points", [])

    # Validate subtitle
    if not subtitle or subtitle == "Key Concepts":
        # Extract from narration - first meaningful phrase
        words = narration.split()[:10] if narration else title.split()[:5]
        subtitle = ' '.join(words) + "..."

    # Validate points - check for generic content
    if all_points_generic(points):
        log_extraction_warning(scene_id, "Intro: Using content-aware bullet extraction")
        points = extract_bullet_points_from_narration(narration, count=3)

    # Generate Manim code for bullets
    bullet_code = "\n".join([
        f'            Text("* {str(p)[:80]}", font_size=24, color=WHITE),'
        for p in points[:4]
    ])

    return {
        "subtitle": subtitle[:100],
        "bullet_points_code": bullet_code
    }


def extract_concept_params(scene: dict) -> dict:
    """Extract parameters for concept template."""
    prompt = f"""Extract parameters for a concept explanation animation.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- main_concept: the central concept (5 words max)
- details: array of 2-3 supporting details (10 words each max)

JSON:"""

    params = call_ollama_json(prompt)

    main_concept = params.get("main_concept", scene['title'][:30])
    details = params.get("details", ["Detail 1", "Detail 2"])

    detail_code = "\n".join([
        f'            Text("- {d[:80]}", font_size=22, color=WHITE),'
        for d in details[:3]
    ])

    return {
        "main_concept": main_concept[:40],
        "detail_points_code": detail_code
    }


def extract_comparison_params(scene: dict) -> dict:
    """Extract parameters for comparison template with content-aware fallback."""
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', '')
    narration = scene.get('narration_text', '')

    prompt = f"""Extract parameters for a comparison animation.

Title: {title}
Visual Description: {scene.get('visual_description', '')}
Narration: {narration}

Return JSON with SPECIFIC content being compared:
- left_label: label for left side (what is being compared)
- left_items: array of 2-3 specific characteristics
- right_label: label for right side (the other thing)
- right_items: array of 2-3 specific characteristics

DO NOT use "Option A/B" or "Item 1/2" - extract actual compared items from content.

JSON:"""

    params = call_ollama_json(prompt, retry_on_fail=True)

    left_label = params.get("left_label", "")
    right_label = params.get("right_label", "")
    left_items = params.get("left_items", [])
    right_items = params.get("right_items", [])

    # Validate labels - extract from title if generic
    if not left_label or left_label in ["Option A", "Left"]:
        # Try to extract from title like "X vs Y" or "X and Y"
        vs_match = re.search(r'(.+?)\s+(?:vs\.?|versus|and|or)\s+(.+)', title, re.IGNORECASE)
        if vs_match:
            left_label = vs_match.group(1).strip()[:25]
            right_label = vs_match.group(2).strip()[:25]
        else:
            left_label = "Approach 1"
            right_label = "Approach 2"

    if not right_label or right_label in ["Option B", "Right"]:
        right_label = "Alternative"

    # Validate items
    if all_points_generic(left_items) or all_points_generic(right_items):
        log_extraction_warning(scene_id, "Comparison: Using content-aware item extraction")
        # Split narration for left/right items
        sentences = re.split(r'[.!?]+', narration)
        mid = len(sentences) // 2
        left_items = [s.strip()[:30] for s in sentences[:mid] if len(s.strip()) > 10][:3]
        right_items = [s.strip()[:30] for s in sentences[mid:] if len(s.strip()) > 10][:3]

        if not left_items:
            left_items = [f"Aspect of {left_label}"]
        if not right_items:
            right_items = [f"Aspect of {right_label}"]

    # Ensure items are strings
    left_items = [str(i)[:30] if not isinstance(i, str) else i[:30] for i in left_items]
    right_items = [str(i)[:30] if not isinstance(i, str) else i[:30] for i in right_items]

    left_code = "\n".join([
        f'            Text("* {i[:30]}", font_size=20, color=WHITE),'
        for i in left_items[:3]
    ])
    right_code = "\n".join([
        f'            Text("* {i[:30]}", font_size=20, color=WHITE),'
        for i in right_items[:3]
    ])

    return {
        "left_label": left_label[:25],
        "right_label": right_label[:25],
        "left_items_code": left_code,
        "right_items_code": right_code
    }


def extract_process_params(scene: dict) -> dict:
    """
    Extract parameters for process flow template.
    Uses retry logic and content-aware fallback to avoid generic content.
    """
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', 'Process')
    visual_desc = scene.get('visual_description', '')
    narration = scene.get('narration_text', '')

    # Primary extraction prompt - more specific instructions
    prompt = f"""Extract SPECIFIC process steps from this content. DO NOT use generic placeholders.

Title: {title}
Visual Description: {visual_desc}
Narration: {narration}

IMPORTANT: Extract the ACTUAL steps mentioned in the narration/description.
DO NOT return generic "Step 1", "Step 2" without real content.

Return JSON with:
- steps: array of [["step_name", "description"], ...] where:
  - step_name: SHORT label (2-4 words) describing the action
  - description: SPECIFIC detail from the content (not generic)
  - 3-5 steps total

Example good output: [["Data Input", "User enters credentials"], ["Validation", "System checks format"], ["Processing", "Backend authenticates"]]
Example bad output: [["Step 1", ""], ["Step 2", ""], ["Step 3", ""]]

JSON:"""

    # First attempt with retry enabled
    params = call_ollama_json(prompt, retry_on_fail=True)
    steps = params.get("steps", [])

    # Check if extraction returned generic content
    if all_steps_generic(steps):
        log_extraction_warning(scene_id, "LLM returned generic steps, trying simplified prompt...")

        # Retry with simpler, more focused prompt
        simplified_prompt = f"""Read this text and list 3-4 key actions or stages mentioned:

"{narration[:500]}"

Return JSON: {{"steps": [["Action1", "detail"], ["Action2", "detail"], ...]}}
JSON:"""

        params = call_ollama_json(simplified_prompt, timeout=PARAM_EXTRACTOR_RETRY_TIMEOUT)
        steps = params.get("steps", [])

    # If still generic, use content-aware extraction from narration
    if all_steps_generic(steps):
        log_extraction_warning(scene_id, "Using content-aware extraction from narration...")
        steps = extract_steps_from_narration(narration, title)

    # Final validation - NEVER return fully generic steps
    if all_steps_generic(steps):
        log_extraction_warning(scene_id, "CRITICAL: Could not extract specific steps, using narration excerpt")
        # Use narration chunks as steps rather than generic placeholders
        narration_words = narration.split() if narration else title.split()
        if len(narration_words) > 15:
            # Split narration into 3 meaningful chunks
            chunk_size = len(narration_words) // 3
            steps = [
                ["Begin", ' '.join(narration_words[:chunk_size])[:40]],
                ["Process", ' '.join(narration_words[chunk_size:2*chunk_size])[:40]],
                ["Complete", ' '.join(narration_words[2*chunk_size:])[:40]]
            ]
        else:
            steps = [[title[:15], narration[:50] if narration else "See demonstration"]]

    # Format and clean steps
    step_data = []
    for step in steps[:5]:
        if isinstance(step, (list, tuple)) and len(step) >= 2:
            name = str(step[0])[:15].strip() or "Step"
            desc = str(step[1])[:40].strip() or ""
            step_data.append([name, desc])
        elif isinstance(step, (list, tuple)) and len(step) == 1:
            step_data.append([str(step[0])[:15].strip(), ""])
        else:
            step_data.append([str(step)[:15].strip(), ""])

    # Ensure at least 2 steps
    while len(step_data) < 2:
        step_data.append(["Continue", "Next phase"])

    return {
        "step_data": repr(step_data)
    }


def extract_example_params(scene: dict) -> dict:
    """Extract parameters for example template."""
    prompt = f"""Extract parameters for an example demonstration animation.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- example_content: the example text or code (max 60 chars)
- result_text: the result or output (max 40 chars)

JSON:"""

    params = call_ollama_json(prompt)

    return {
        "example_content": params.get("example_content", "Example content here")[:60],
        "result_text": params.get("result_text", "Result: Success")[:40]
    }


def extract_conclusion_params(scene: dict) -> dict:
    """Extract parameters for conclusion template with content-aware fallback."""
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', '')
    narration = scene.get('narration_text', '')

    prompt = f"""Extract parameters for a conclusion animation.

Title: {title}
Visual Description: {scene.get('visual_description', '')}
Narration: {narration}

Return JSON with SPECIFIC content:
- takeaways: array of 3-4 key takeaways (10 words each max) - actual lessons from content
- final_message: inspiring final message (8 words max)

DO NOT use "Key point 1", "Key point 2" - use actual takeaways from the narration.

JSON:"""

    params = call_ollama_json(prompt, retry_on_fail=True)

    takeaways = params.get("takeaways", [])
    final_message = params.get("final_message", "")

    # Validate takeaways
    if all_points_generic(takeaways):
        log_extraction_warning(scene_id, "Conclusion: Using content-aware takeaway extraction")
        takeaways = extract_bullet_points_from_narration(narration, count=3)

    # Validate final message
    if not final_message or final_message == "Thank you for watching!":
        # Create a relevant closing based on title
        if title:
            final_message = f"Now you understand {title[:25]}!"
        else:
            final_message = "Apply these concepts today!"

    takeaway_code = "\n".join([
        f'            Text("{i+1}. {str(t)[:45]}", font_size=26, color=WHITE),'
        for i, t in enumerate(takeaways[:4])
    ])

    return {
        "takeaway_points_code": takeaway_code,
        "final_message": final_message[:50]
    }


# ─── Advanced Template Parameter Extractors ─────────────────────────────────

def extract_data_chart_params(scene: dict) -> dict:
    """Extract parameters for data chart template."""
    prompt = f"""Extract data for a bar chart animation.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- values: array of 4-6 numbers (e.g., [45, 78, 32, 91, 56])
- labels: array of corresponding labels (max 8 chars each)

JSON:"""

    params = call_ollama_json(prompt)

    values = params.get("values", [65, 45, 80, 55, 70])[:6]
    labels = params.get("labels", ["A", "B", "C", "D", "E"])[:6]

    # Ensure values are numbers
    values = [int(v) if isinstance(v, (int, float)) else 50 for v in values]
    labels = [str(lbl)[:8] for lbl in labels]

    return {
        "chart_values": repr(values),
        "chart_labels": repr(labels)
    }


def extract_math_formula_params(scene: dict) -> dict:
    """Extract parameters for math formula template."""
    prompt = f"""Extract a mathematical equation from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- equation: LaTeX equation (e.g., "E = mc^2" or "\\\\frac{{a}}{{b}}")
- explanation: brief explanation of the equation (max 60 chars)

JSON:"""

    params = call_ollama_json(prompt)

    equation = params.get("equation", "y = mx + b")
    explanation = params.get("explanation", "A fundamental equation")

    # Clean equation for LaTeX
    equation = equation.replace("\\", "\\\\").replace('"', '')[:80]

    return {
        "equation": equation,
        "explanation": explanation[:60]
    }


def extract_equation_derivation_params(scene: dict) -> dict:
    """Extract parameters for equation derivation template."""
    prompt = f"""Extract step-by-step equation derivation from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- steps: array of [step_label, latex_equation] pairs showing the derivation
  e.g., [["Original", "ax^2 + bx + c = 0"], ["Divide by a", "x^2 + \\\\frac{{b}}{{a}}x = -\\\\frac{{c}}{{a}}"], ...]
  (3-5 steps, each equation in valid LaTeX)

JSON:"""

    params = call_ollama_json(prompt)

    steps = params.get("steps", [
        ["Start", "ax + b = c"],
        ["Subtract b", "ax = c - b"],
        ["Divide by a", "x = \\frac{c - b}{a}"]
    ])

    # Validate and clean steps
    formatted_steps = []
    for step in steps[:5]:
        if isinstance(step, (list, tuple)) and len(step) >= 2:
            label = str(step[0])[:20]
            # Clean LaTeX - ensure proper escaping
            latex = str(step[1]).replace('"', '').replace("'", "")
            # Don't double-escape if already escaped
            if '\\\\' not in latex:
                latex = latex.replace('\\', '\\\\')
            formatted_steps.append([label, latex])

    if not formatted_steps:
        formatted_steps = [
            ["Start", "ax + b = c"],
            ["Isolate", "ax = c - b"],
            ["Solve", "x = \\\\frac{c - b}{a}"]
        ]

    return {
        "derivation_steps": repr(formatted_steps)
    }


def extract_graph_visualization_params(scene: dict) -> dict:
    """Extract parameters for graph visualization template."""
    prompt = f"""Extract function graph parameters from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- function_latex: LaTeX representation of the function (e.g., "f(x) = x^2 - 2x + 1")
- function_code: Python lambda code for the function (e.g., "x**2 - 2*x + 1")
- x_range: [min, max, step] for x-axis (e.g., [-5, 5, 1])
- y_range: [min, max, step] for y-axis (e.g., [-2, 10, 1])
- x_label: x-axis label (e.g., "x")
- y_label: y-axis label (e.g., "y")
- key_points: array of [x, y, "label"] for important points (e.g., [[1, 0, "(1, 0)"]])

JSON:"""

    params = call_ollama_json(prompt)

    function_latex = params.get("function_latex", "f(x) = x^2")
    function_code = params.get("function_code", "x**2")
    x_range = params.get("x_range", [-5, 5, 1])
    y_range = params.get("y_range", [-2, 10, 1])
    x_label = params.get("x_label", "x")
    y_label = params.get("y_label", "y")
    key_points = params.get("key_points", [[0, 0, "(0, 0)"]])

    # Clean and validate
    function_latex = function_latex.replace('"', '').replace("'", "")[:50]
    function_code = function_code.replace('"', '').replace("'", "")[:50]

    # Ensure ranges are valid
    if not isinstance(x_range, list) or len(x_range) != 3:
        x_range = [-5, 5, 1]
    if not isinstance(y_range, list) or len(y_range) != 3:
        y_range = [-2, 10, 1]

    # Validate key_points format
    valid_points = []
    for pt in key_points[:4]:
        if isinstance(pt, (list, tuple)) and len(pt) >= 3:
            try:
                x, y = float(pt[0]), float(pt[1])
                label = str(pt[2])[:15]
                valid_points.append([x, y, label])
            except (ValueError, TypeError):
                pass

    if not valid_points:
        valid_points = [[0, 0, "(0, 0)"]]

    return {
        "function_latex": function_latex,
        "function_code": function_code,
        "x_range": repr(x_range),
        "y_range": repr(y_range),
        "x_label": x_label,
        "y_label": y_label,
        "key_points": repr(valid_points)
    }


def extract_geometric_theorem_params(scene: dict) -> dict:
    """Extract parameters for geometric theorem template."""
    prompt = f"""Extract geometric theorem parameters from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- theorem_latex: The main theorem formula in LaTeX (e.g., "a^2 + b^2 = c^2")
- shape_type: one of "triangle", "circle", or "polygon"
- vertices: array of [x, y, 0] coordinates for shape vertices (e.g., [[0, 0, 0], [3, 0, 0], [3, 2, 0]])
- side_labels: array of [[x, y, 0], "label"] for labeling sides (e.g., [[[1.5, -0.3, 0], "a"], [[3.3, 1, 0], "b"]])
- proof_steps: array of LaTeX proof steps (e.g., ["a^2 = 9", "b^2 = 16", "c^2 = a^2 + b^2 = 25"])

JSON:"""

    params = call_ollama_json(prompt)

    theorem_latex = params.get("theorem_latex", "a^2 + b^2 = c^2")
    shape_type = params.get("shape_type", "triangle")
    vertices = params.get("vertices", [[0, 0, 0], [3, 0, 0], [0, 2, 0]])
    side_labels = params.get("side_labels", [
        [[1.5, -0.3, 0], "a"],
        [[-0.3, 1, 0], "b"],
        [[1.8, 1.2, 0], "c"]
    ])
    proof_steps = params.get("proof_steps", [
        "a = 3",
        "b = 4",
        "c = \\sqrt{a^2 + b^2} = 5"
    ])

    # Validate shape_type
    if shape_type not in ["triangle", "circle", "polygon"]:
        shape_type = "triangle"

    # Clean theorem latex
    theorem_latex = theorem_latex.replace('"', '').replace("'", "")
    if '\\\\' not in theorem_latex:
        theorem_latex = theorem_latex.replace('\\', '\\\\')

    # Clean proof steps
    clean_proof = []
    for step in proof_steps[:5]:
        step_str = str(step).replace('"', '').replace("'", "")
        if '\\\\' not in step_str:
            step_str = step_str.replace('\\', '\\\\')
        clean_proof.append(step_str)

    return {
        "theorem_latex": theorem_latex,
        "shape_type": shape_type,
        "vertices": repr(vertices),
        "side_labels": repr(side_labels),
        "proof_steps": repr(clean_proof)
    }


def extract_matrix_operation_params(scene: dict) -> dict:
    """Extract parameters for matrix operation template."""
    prompt = f"""Extract matrix operation parameters from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- matrix_a: 2D array for first matrix (e.g., [[1, 2], [3, 4]])
- matrix_b: 2D array for second matrix (null if not applicable)
- operation: one of "multiply", "add", "determinant", "inverse"
- result_matrix: 2D array for result (if matrix result)
- scalar_result: string for scalar result like determinant (e.g., "-2")

JSON:"""

    params = call_ollama_json(prompt)

    matrix_a = params.get("matrix_a", [[1, 2], [3, 4]])
    matrix_b = params.get("matrix_b", None)
    operation = params.get("operation", "multiply")
    result_matrix = params.get("result_matrix", [[7, 10], [15, 22]])
    scalar_result = params.get("scalar_result", "")

    # Validate operation
    if operation not in ["multiply", "add", "determinant", "inverse"]:
        operation = "multiply"

    # Ensure matrices are valid 2D arrays
    def validate_matrix(m, default):
        if not isinstance(m, list) or not m:
            return default
        if not all(isinstance(row, list) for row in m):
            return default
        return m

    matrix_a = validate_matrix(matrix_a, [[1, 2], [3, 4]])
    matrix_b = validate_matrix(matrix_b, [[5, 6], [7, 8]]) if matrix_b else None
    result_matrix = validate_matrix(result_matrix, [[19, 22], [43, 50]])

    return {
        "matrix_a": repr(matrix_a),
        "matrix_b": repr(matrix_b) if matrix_b else "None",
        "operation": operation,
        "result_matrix": repr(result_matrix),
        "scalar_result": str(scalar_result)[:20]
    }


def extract_timeline_params(scene: dict) -> dict:
    """Extract parameters for timeline template."""
    prompt = f"""Extract timeline events from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- events: array of [year/label, event_description] pairs
  e.g., [["2020", "Event 1"], ["2021", "Event 2"], ...]
  (4-6 events, labels max 10 chars, events max 20 chars)

JSON:"""

    params = call_ollama_json(prompt)

    events = params.get("events", [
        ["Step 1", "First event"],
        ["Step 2", "Second event"],
        ["Step 3", "Third event"],
        ["Step 4", "Fourth event"]
    ])

    # Ensure proper format
    formatted_events = []
    for e in events[:6]:
        if isinstance(e, (list, tuple)) and len(e) >= 2:
            formatted_events.append([str(e[0])[:10], str(e[1])[:20]])
        elif isinstance(e, str):
            formatted_events.append([str(len(formatted_events)+1), str(e)[:20]])

    if not formatted_events:
        formatted_events = [["1", "Event 1"], ["2", "Event 2"], ["3", "Event 3"]]

    return {
        "timeline_events": repr(formatted_events)
    }


def extract_diagram_params(scene: dict) -> dict:
    """Extract parameters for diagram template."""
    prompt = f"""Extract a central concept and connected items from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- center_node: the central concept (max 15 chars)
- connected_nodes: array of 4-6 related concepts (max 15 chars each)

JSON:"""

    params = call_ollama_json(prompt)

    center = params.get("center_node", scene['title'][:15])
    connected = params.get("connected_nodes", ["Feature 1", "Feature 2", "Feature 3", "Feature 4"])

    connected = [str(n)[:15] for n in connected[:6]]

    return {
        "center_node": str(center)[:15],
        "connected_nodes": repr(connected)
    }


def extract_metrics_params(scene: dict) -> dict:
    """Extract parameters for metrics template."""
    prompt = f"""Extract numeric metrics from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- metrics: array of [label, value, unit] tuples
  e.g., [["Users", 5000, "K"], ["Revenue", 120, "M"], ...]
  (3-4 metrics, labels max 15 chars, values as numbers, units max 8 chars)

JSON:"""

    params = call_ollama_json(prompt)

    metrics = params.get("metrics", [
        ["Metric 1", 100, "%"],
        ["Metric 2", 250, "K"],
        ["Metric 3", 50, "M"]
    ])

    # Ensure proper format
    formatted = []
    for m in metrics[:4]:
        if isinstance(m, (list, tuple)) and len(m) >= 3:
            formatted.append([str(m[0])[:15], int(m[1]) if isinstance(m[1], (int, float)) else 100, str(m[2])[:8]])
        elif isinstance(m, (list, tuple)) and len(m) >= 2:
            formatted.append([str(m[0])[:15], int(m[1]) if isinstance(m[1], (int, float)) else 100, ""])

    if not formatted:
        formatted = [["Value 1", 100, "%"], ["Value 2", 200, "K"], ["Value 3", 50, "M"]]

    return {
        "metrics_data": repr(formatted)
    }


def extract_hierarchy_params(scene: dict) -> dict:
    """Extract parameters for hierarchy template."""
    prompt = f"""Extract a hierarchy structure from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- root_node: the top-level item (max 20 chars)
- child_nodes: array of 3-5 child items (max 12 chars each)

JSON:"""

    params = call_ollama_json(prompt)

    root = params.get("root_node", scene['title'][:20])
    children = params.get("child_nodes", ["Item 1", "Item 2", "Item 3"])

    children = [str(c)[:12] for c in children[:5]]

    return {
        "root_node": str(root)[:20],
        "child_nodes": repr(children)
    }


# ─── Claude-Style Template Parameter Extractors ─────────────────────────────

def extract_visual_explanation_params(scene: dict) -> dict:
    """Extract parameters for Claude-style visual explanation template with content-aware fallback."""
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', '')
    narration = scene.get('narration_text', '')

    prompt = f"""Extract a comparison with two options from this content.

Title: {title}
Visual Description: {scene.get('visual_description', '')}
Narration: {narration}

Return JSON with SPECIFIC content from the narration:
- option_a_label: name of first option (max 20 chars)
- option_a_points: array of 3 points supporting option A (max 35 chars each)
- option_b_label: name of second option (max 20 chars)
- option_b_points: array of 3 points supporting option B (max 35 chars each)
- recommendation: recommendation text (max 50 chars)

DO NOT use "Option A/B" or "Point 1/2/3" - extract actual options and points.

JSON:"""

    params = call_ollama_json(prompt, retry_on_fail=True)

    option_a_label = params.get("option_a_label", "")
    option_b_label = params.get("option_b_label", "")
    option_a_points = params.get("option_a_points", [])
    option_b_points = params.get("option_b_points", [])
    recommendation = params.get("recommendation", "")

    # Validate labels
    if not option_a_label or option_a_label == "Option A":
        # Try to extract from title
        vs_match = re.search(r'(.+?)\s+(?:vs\.?|versus|and|or)\s+(.+)', title, re.IGNORECASE)
        if vs_match:
            option_a_label = vs_match.group(1).strip()[:20]
            option_b_label = vs_match.group(2).strip()[:20]
        else:
            option_a_label = "Approach"
            option_b_label = "Alternative"

    if not option_b_label or option_b_label == "Option B":
        option_b_label = "Alternative"

    # Validate points
    if all_points_generic(option_a_points) or all_points_generic(option_b_points):
        log_extraction_warning(scene_id, "Visual explanation: Using content-aware point extraction")
        points = extract_bullet_points_from_narration(narration, count=6)
        mid = len(points) // 2
        option_a_points = points[:mid] if mid > 0 else points[:3]
        option_b_points = points[mid:] if mid > 0 else points[:3]

    # Validate recommendation
    if not recommendation or "Consider both" in recommendation:
        recommendation = f"Choose based on your {title[:20]} needs"

    # Ensure points are strings
    option_a_points = [str(p)[:35] for p in option_a_points[:3]]
    option_b_points = [str(p)[:35] for p in option_b_points[:3]]

    # Ensure at least one point each
    if not option_a_points:
        option_a_points = [f"Key aspect of {option_a_label}"]
    if not option_b_points:
        option_b_points = [f"Key aspect of {option_b_label}"]

    # Generate Manim code for points
    option_a_code = "\n".join([
        f'            Text("• {p}", font_size=18, color="#c0caf5"),'
        for p in option_a_points
    ])
    option_b_code = "\n".join([
        f'            Text("• {p}", font_size=18, color="#c0caf5"),'
        for p in option_b_points
    ])

    return {
        "option_a_label": option_a_label[:20],
        "option_b_label": option_b_label[:20],
        "option_a_points_code": option_a_code,
        "option_b_points_code": option_b_code,
        "recommendation": recommendation[:50]
    }


def extract_info_card_params(scene: dict) -> dict:
    """Extract parameters for Claude-style info card template with content-aware fallback."""
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', '')
    narration = scene.get('narration_text', '')

    prompt = f"""Extract overview and key points from this content.

Title: {title}
Visual Description: {scene.get('visual_description', '')}
Narration: {narration}

Return JSON with SPECIFIC content from the narration:
- overview_text: main explanation (max 80 chars) - summarize the key idea
- key_points: array of 3-4 important points (max 40 chars each) - actual points mentioned

DO NOT use "Point 1", "Point 2" - extract actual key points from content.

JSON:"""

    params = call_ollama_json(prompt, retry_on_fail=True)

    overview = params.get("overview_text", "")
    key_points = params.get("key_points", [])

    # Validate overview
    if not overview or overview == "This topic covers important concepts.":
        # Extract first meaningful sentence from narration
        sentences = re.split(r'[.!?]+', narration)
        overview = next((s.strip()[:80] for s in sentences if len(s.strip()) > 20), title)

    # Validate key points
    if all_points_generic(key_points):
        log_extraction_warning(scene_id, "Info card: Using content-aware point extraction")
        key_points = extract_bullet_points_from_narration(narration, count=4)

    # Ensure points are strings
    key_points = [str(p)[:40] for p in key_points[:4]]

    # Ensure at least one point
    if not key_points:
        key_points = [narration[:40] if narration else title[:40]]

    # Generate Manim code for points
    points_code = "\n".join([
        f'            Text("• {p}", font_size=18, color="#c0caf5"),'
        for p in key_points
    ])

    return {
        "overview_text": overview[:80],
        "key_points_code": points_code
    }


def extract_decision_tree_params(scene: dict) -> dict:
    """Extract parameters for decision tree template."""
    prompt = f"""Extract process steps from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- steps: array of [step_title, step_description] pairs
  (3-5 steps, titles max 25 chars)

JSON:"""

    params = call_ollama_json(prompt)

    steps = params.get("steps", [
        ["Step 1", "First action"],
        ["Step 2", "Second action"],
        ["Step 3", "Final action"]
    ])

    # Ensure proper format
    formatted_steps = []
    for s in steps[:5]:
        if isinstance(s, (list, tuple)) and len(s) >= 2:
            formatted_steps.append([str(s[0])[:25], str(s[1])[:40]])
        elif isinstance(s, str):
            formatted_steps.append([str(s)[:25], ""])

    if not formatted_steps:
        formatted_steps = [["Start", ""], ["Process", ""], ["End", ""]]

    return {
        "steps_data": repr(formatted_steps)
    }


# ─── Main Generator ─────────────────────────────────────────────────────────

PARAM_EXTRACTORS = {
    "intro": extract_intro_params,
    "concept": extract_concept_params,
    "comparison": extract_comparison_params,
    "process": extract_process_params,
    "example": extract_example_params,
    "conclusion": extract_conclusion_params,
    # Advanced templates
    "data_chart": extract_data_chart_params,
    "math_formula": extract_math_formula_params,
    "timeline": extract_timeline_params,
    "diagram": extract_diagram_params,
    "metrics": extract_metrics_params,
    "hierarchy": extract_hierarchy_params,
    # LaTeX-enhanced templates
    "equation_derivation": extract_equation_derivation_params,
    "graph_visualization": extract_graph_visualization_params,
    "geometric_theorem": extract_geometric_theorem_params,
    "matrix_operation": extract_matrix_operation_params,
    # Claude-style templates
    "visual_explanation": extract_visual_explanation_params,
    "info_card": extract_info_card_params,
    "decision_tree": extract_decision_tree_params,
}


def generate_scene_code(scene: dict) -> str:
    """
    Generate Manim code from scene data using templates.
    Extracts parameters from visual_description using LLM.
    """
    scene_type = scene.get("scene_type", "concept")
    scene_id = scene["scene_id"]
    title = scene["title"]

    # Get template
    template = SCENE_TEMPLATES.get(scene_type, SCENE_TEMPLATES["concept"])

    # Extract parameters
    extractor = PARAM_EXTRACTORS.get(scene_type, extract_concept_params)
    params = extractor(scene)

    # Add common params
    params["scene_id"] = scene_id
    params["title"] = title[:45]  # Limit title length

    # Fill template
    try:
        code = template.format(**params)
        return code
    except KeyError as e:
        print(f"  Template error: missing param {e}")
        return None


if __name__ == "__main__":
    # Test
    test_scene = {
        "scene_id": 1,
        "scene_type": "intro",
        "title": "Introduction to Python",
        "narration_text": "Python is a powerful programming language used worldwide.",
        "visual_description": "Title with bullet points showing Python features"
    }

    code = generate_scene_code(test_scene)
    print(code)
