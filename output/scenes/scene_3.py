from manim import *

class Scene3(Scene):
    def construct(self):
        title = Text("YouTube AI Agent Framework", font_size=40, color=BLUE).to_edge(UP, buff=0.4)
        self.play(Write(title))
        self.wait(0.5)

        # Input (positioned above the agent pipeline)
        input_box = Rectangle(width=2.8, height=0.9, color=WHITE, fill_opacity=0.1)
        input_text = Text("Research Paper / Abstract", font_size=18)
        input_text.move_to(input_box.get_center())
        input_grp = VGroup(input_box, input_text).move_to(LEFT * 4.5 + UP * 1.8)

        # Output (positioned above the agent pipeline, right side)
        output_box = Rectangle(width=2.8, height=0.9, color=YELLOW, fill_opacity=0.2)
        output_text = Text("Educational Video (MP4)", font_size=18, color=YELLOW_B)
        output_text.move_to(output_box.get_center())
        output_grp = VGroup(output_box, output_text).move_to(RIGHT * 4.5 + UP * 1.8)

        self.play(FadeIn(input_grp))
        self.wait(0.3)

        # Four agents in a row
        agent_data = [
            ("Research\n& Script", BLUE),
            ("Animation\n(Manim)", GREEN),
            ("TTS\nNarration", ORANGE),
            ("Video\nAssembly", PURPLE),
        ]
        agents = VGroup()
        for label, color in agent_data:
            box = RoundedRectangle(corner_radius=0.2, width=2.2, height=1.3,
                                   color=color, fill_opacity=0.25)
            txt = Text(label, font_size=20, color=color)
            txt.move_to(box.get_center())
            agents.add(VGroup(box, txt))

        agents.arrange(RIGHT, buff=0.25).move_to(ORIGIN + DOWN * 0.2)
        self.play(FadeIn(agents, shift=UP * 0.3, lag_ratio=0.2))
        self.wait(0.4)

        # Arrows between agents (buff=0.15 to stop at box edge)
        arrows = VGroup()
        for i in range(len(agents) - 1):
            arr = Arrow(
                agents[i].get_right(), agents[i + 1].get_left(),
                buff=0.15, color=GREY_B, stroke_width=3
            )
            arrows.add(arr)
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2))

        # Input → first agent (diagonal arrow, buff=0.2 to stop at edges)
        arr_in = Arrow(input_grp.get_bottom(), agents[0].get_top(),
                       buff=0.2, color=WHITE, stroke_width=3)
        # Last agent → output (diagonal arrow, buff=0.2 to stop at edges)
        arr_out = Arrow(agents[-1].get_top(), output_grp.get_bottom(),
                        buff=0.2, color=YELLOW, stroke_width=3)
        self.play(GrowArrow(arr_in), FadeIn(output_grp))
        self.play(GrowArrow(arr_out))
        self.wait(2.5)

        self.play(FadeOut(VGroup(title, input_grp, output_grp, agents, arrows, arr_in, arr_out)))
