from manim import *

class Scene5(Scene):
    def construct(self):
        title = Text("Framework in Action", font_size=42, color=BLUE).to_edge(UP, buff=0.3)
        self.play(Write(title))
        self.wait(0.3)

        # Pipeline steps as vertical flow
        steps = [
            ("Input: Python Programming Abstract", WHITE),
            ("Agent 1 → Script: 6 structured scenes", BLUE_B),
            ("Agent 2 → Manim animations per scene", GREEN_B),
            ("Agent 3 → Hindi/English narration WAVs", ORANGE),
            ("Agent 4 → Final MP4 video assembled", YELLOW_B),
        ]

        step_grps = VGroup()
        for i, (text, color) in enumerate(steps):
            circle = Circle(radius=0.28, color=color, fill_opacity=0.8)
            num = Text(str(i + 1), font_size=20, color=BLACK, weight=BOLD)
            num.move_to(circle.get_center())
            label = Text(text, font_size=22, color=color)
            row = VGroup(VGroup(circle, num), label).arrange(RIGHT, buff=0.35)
            step_grps.add(row)

        step_grps.arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to(DOWN * 0.4)

        for i, step in enumerate(step_grps):
            self.play(FadeIn(step, shift=RIGHT * 0.2), run_time=0.5)
            if i < len(step_grps) - 1:
                connector = Line(
                    step[0].get_bottom() + DOWN * 0.05,
                    step_grps[i + 1][0].get_top() + UP * 0.05,
                    color=GREY, stroke_width=2
                )
                self.play(Create(connector), run_time=0.25)
            self.wait(0.3)

        # Outcome callout
        outcome = Text(
            "Result: Professional video in minutes, not weeks",
            font_size=24, color=GREEN_B
        ).to_edge(DOWN, buff=0.45)
        box = SurroundingRectangle(outcome, color=GREEN, buff=0.15, corner_radius=0.1)
        self.play(Write(outcome), Create(box))
        self.wait(2.5)

        self.play(FadeOut(VGroup(title, step_grps, outcome, box)))
