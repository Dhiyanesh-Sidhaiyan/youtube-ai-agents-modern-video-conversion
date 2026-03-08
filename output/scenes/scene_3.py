from manim import *

class Scene3(Scene):
    def construct(self):
        # Title
        title = Text("Real-World Failures: Lessons Learned", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
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
            "Chevrolet sale error, Air Canada chatbot mishap",
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
        result_text = Text("Risks of poor LLM prompts", font_size=22, color=GREEN_B, weight=BOLD)
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
