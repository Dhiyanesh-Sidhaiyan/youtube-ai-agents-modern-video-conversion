"""
Generic Parameterized Manim Scene Templates
These templates are used to dynamically generate Manim scenes based on content.
Each template type handles different visual presentations.
"""

import json
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
PARAM_EXTRACTOR_MODEL = "phi4"


# ─── Scene Templates ────────────────────────────────────────────────────────

SCENE_TEMPLATES = {

    "intro": '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
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
'''
}


# ─── Parameter Extraction ───────────────────────────────────────────────────

def call_ollama_json(prompt: str) -> dict:
    """Call Ollama and parse JSON response."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": PARAM_EXTRACTOR_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 1000}
            },
            timeout=60
        )
        response.raise_for_status()
        text = response.json().get("response", "")

        # Extract JSON from response
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"  Param extraction error: {e}")
    return {}


def extract_intro_params(scene: dict) -> dict:
    """Extract parameters for intro template."""
    prompt = f"""Extract parameters for an intro animation from this scene.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- subtitle: 1-line subtitle (10 words max)
- bullet_points: array of 3-4 key points (8 words each max)

JSON:"""

    params = call_ollama_json(prompt)

    # Defaults
    subtitle = params.get("subtitle", "Key Concepts")
    points = params.get("bullet_points", ["Point 1", "Point 2", "Point 3"])

    # Generate Manim code for bullets
    bullet_code = "\n".join([
        f'            Text("* {p[:50]}", font_size=24, color=WHITE),'
        for p in points[:4]
    ])

    return {
        "subtitle": subtitle[:60],
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
        f'            Text("- {d[:50]}", font_size=22, color=WHITE),'
        for d in details[:3]
    ])

    return {
        "main_concept": main_concept[:40],
        "detail_points_code": detail_code
    }


def extract_comparison_params(scene: dict) -> dict:
    """Extract parameters for comparison template."""
    prompt = f"""Extract parameters for a comparison animation.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- left_label: label for left side
- left_items: array of 2-3 items
- right_label: label for right side
- right_items: array of 2-3 items

JSON:"""

    params = call_ollama_json(prompt)

    left_label = params.get("left_label", "Option A")
    right_label = params.get("right_label", "Option B")
    left_items = params.get("left_items", ["Item 1", "Item 2"])
    right_items = params.get("right_items", ["Item 1", "Item 2"])

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
    """Extract parameters for process flow template."""
    prompt = f"""Extract parameters for a process flow animation.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- steps: array of tuples [["Step 1", "description"], ["Step 2", "description"], ...]
  (3-5 steps, step names max 12 chars)

JSON:"""

    params = call_ollama_json(prompt)

    steps = params.get("steps", [["Step 1", ""], ["Step 2", ""], ["Step 3", ""]])

    # Format as Python list
    step_data = [[s[0][:15], s[1][:30] if len(s) > 1 else ""] for s in steps[:5]]

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
    """Extract parameters for conclusion template."""
    prompt = f"""Extract parameters for a conclusion animation.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- takeaways: array of 3-4 key takeaways (10 words each max)
- final_message: inspiring final message (8 words max)

JSON:"""

    params = call_ollama_json(prompt)

    takeaways = params.get("takeaways", ["Key point 1", "Key point 2", "Key point 3"])
    final_message = params.get("final_message", "Thank you for watching!")

    takeaway_code = "\n".join([
        f'            Text("{i+1}. {t[:45]}", font_size=26, color=WHITE),'
        for i, t in enumerate(takeaways[:4])
    ])

    return {
        "takeaway_points_code": takeaway_code,
        "final_message": final_message[:50]
    }


# ─── Main Generator ─────────────────────────────────────────────────────────

PARAM_EXTRACTORS = {
    "intro": extract_intro_params,
    "concept": extract_concept_params,
    "comparison": extract_comparison_params,
    "process": extract_process_params,
    "example": extract_example_params,
    "conclusion": extract_conclusion_params
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
