from manim import *

class Scene1(Scene):
    def construct(self):
        # Title
        title = Text("Indian Higher Education", font_size=44, color=BLUE).to_edge(UP, buff=0.4)
        self.play(Write(title))
        self.wait(0.5)

        # Stats box
        stat1 = Text("40 Million+", font_size=56, color=YELLOW)
        label1 = Text("Students Enrolled", font_size=28, color=WHITE)
        grp1 = VGroup(stat1, label1).arrange(DOWN, buff=0.15).move_to(LEFT * 3 + UP * 0.5)

        stat2 = Text("NEP 2020", font_size=48, color=GREEN)
        label2 = Text("Mandates Tech-Integrated Teaching", font_size=22, color=WHITE)
        grp2 = VGroup(stat2, label2).arrange(DOWN, buff=0.15).move_to(RIGHT * 2 + UP * 0.5)

        self.play(FadeIn(grp1, shift=UP))
        self.wait(0.4)
        self.play(FadeIn(grp2, shift=UP))
        self.wait(0.8)

        # Divider
        divider = Line(UP * 2, DOWN * 0.5, color=GREY).move_to(ORIGIN + UP * 0.5)
        self.play(Create(divider))

        # Problem bar
        problem = Rectangle(width=10, height=1.2, color=RED, fill_opacity=0.2)
        problem_text = Text(
            "Challenge: Educators lack tools to create multimedia content",
            font_size=22, color=RED_B
        )
        prob_grp = VGroup(problem, problem_text).arrange(DOWN, buff=0).move_to(DOWN * 2)
        self.play(FadeIn(prob_grp))
        self.wait(1)

        # Highlight NEP vs reality gap
        arrow = Arrow(grp2.get_bottom(), prob_grp.get_top(), color=ORANGE, buff=0.1)
        gap_label = Text("Gap ↓", font_size=26, color=ORANGE).next_to(arrow, RIGHT, buff=0.1)
        self.play(GrowArrow(arrow), Write(gap_label))
        self.wait(2)

        self.play(FadeOut(VGroup(title, grp1, grp2, divider, prob_grp, arrow, gap_label)))
