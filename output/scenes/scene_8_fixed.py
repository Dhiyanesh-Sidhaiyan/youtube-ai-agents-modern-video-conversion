from manim import *

class Scene8(Scene):
    def construct(self):
        # Title with emphasis
        title = Text("Deterministic vs. Stochastic Outputs", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)
        self.wait(0.3)

        # Left side with gradient border effect
        left_box = RoundedRectangle(
            corner_radius=0.2, width=5, height=3.5,
            color=RED_C, fill_opacity=0.1, stroke_width=3
        )
        left_header = Text("Deterministic Outputs", font_size=28, color=RED_C, weight=BOLD)
        left_underline = Line(LEFT * 1.5, RIGHT * 1.5, color=RED_C, stroke_width=2)
        left_items = VGroup(
            Text("* Calculator", font_size=20, color=WHITE),
            Text("* 1+1=2", font_size=20, color=WHITE),
            Text("* Consistent Results", font_size=20, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)

        left_content = VGroup(left_header, left_underline, left_items).arrange(DOWN, buff=0.2)
        left_grp = VGroup(left_box, left_content).move_to(LEFT * 3 + DOWN * 0.2)
        left_content.move_to(left_box.get_center())

        # Right side
        right_box = RoundedRectangle(
            corner_radius=0.2, width=5, height=3.5,
            color=GREEN_C, fill_opacity=0.1, stroke_width=3
        )
        right_header = Text("Stochastic Outputs", font_size=28, color=GREEN_C, weight=BOLD)
        right_underline = Line(LEFT * 1.5, RIGHT * 1.5, color=GREEN_C, stroke_width=2)
        right_items = VGroup(
            Text("* LLM (Large Language Model)", font_size=20, color=WHITE),
            Text("* Varied Responses", font_size=20, color=WHITE),
            Text("* Inconsistent Results", font_size=20, color=WHITE),
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
