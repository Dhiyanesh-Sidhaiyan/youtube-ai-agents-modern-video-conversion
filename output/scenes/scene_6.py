from manim import *

class Scene6(Scene):
    def construct(self):
        title = Text("Impact & Conclusion", font_size=44, color=BLUE).to_edge(UP, buff=0.3)
        self.play(Write(title))
        self.wait(0.4)

        # Impact metrics
        metrics = [
            ("40M+", "Students reached", GREEN),
            ("21", "Indian languages", ORANGE),
            ("100%", "Open Source", YELLOW),
            ("NEP 2020", "Aligned", BLUE),
        ]

        metric_grps = VGroup()
        for value, label, color in metrics:
            val_text = Text(value, font_size=52, color=color, weight=BOLD)
            lbl_text = Text(label, font_size=22, color=WHITE)
            grp = VGroup(val_text, lbl_text).arrange(DOWN, buff=0.15)
            box = SurroundingRectangle(grp, color=color, buff=0.25,
                                        corner_radius=0.15, fill_opacity=0.1)
            metric_grps.add(VGroup(box, grp))

        metric_grps.arrange_in_grid(2, 2, buff=0.5).move_to(ORIGIN + DOWN * 0.4)

        for m in metric_grps:
            self.play(FadeIn(m, scale=0.8), run_time=0.5)
        self.wait(0.6)

        # Final message
        finale = Text(
            "Empowering Every Educator Across India",
            font_size=28, color=YELLOW, weight=BOLD
        ).to_edge(DOWN, buff=0.5)
        underline = Line(finale.get_left(), finale.get_right(),
                         color=YELLOW, stroke_width=2).next_to(finale, DOWN, buff=0.05)
        self.play(Write(finale), Create(underline))
        self.wait(3)

        self.play(FadeOut(VGroup(title, metric_grps, finale, underline)))
