from manim import *

class Scene2(Scene):
    def construct(self):
        title = Text("Video-Based Learning", font_size=44, color=BLUE).to_edge(UP, buff=0.4)
        self.play(Write(title))
        self.wait(0.4)

        # Left: Traditional teaching
        left_box = Rectangle(width=4.2, height=3.5, color=GREY, fill_opacity=0.15)
        left_label = Text("Traditional\nTeaching", font_size=28, color=GREY_B)
        left_items = VGroup(
            Text("• Blackboard", font_size=22),
            Text("• One-way lecture", font_size=22),
            Text("• Limited reach", font_size=22),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        left_content = VGroup(left_label, left_items).arrange(DOWN, buff=0.3)
        left_grp = VGroup(left_box, left_content).move_to(LEFT * 2.8 + DOWN * 0.3)
        left_content.move_to(left_box.get_center())

        # Right: Video learning
        right_box = Rectangle(width=4.2, height=3.5, color=GREEN, fill_opacity=0.15)
        right_label = Text("Video Learning", font_size=28, color=GREEN_B)
        right_items = VGroup(
            Text("• Visual + Audio", font_size=22),
            Text("• Replayable anytime", font_size=22),
            Text("• Reaches millions", font_size=22),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        right_content = VGroup(right_label, right_items).arrange(DOWN, buff=0.3)
        right_grp = VGroup(right_box, right_content).move_to(RIGHT * 2.8 + DOWN * 0.3)
        right_content.move_to(right_box.get_center())

        vs = Text("VS", font_size=36, color=YELLOW).move_to(ORIGIN + DOWN * 0.3)

        self.play(FadeIn(left_grp, shift=LEFT * 0.5))
        self.play(Write(vs))
        self.play(FadeIn(right_grp, shift=RIGHT * 0.5))
        self.wait(0.8)

        # Highlight the barrier
        barrier = Text(
            "But: 90% of educators lack technical skills to produce video",
            font_size=22, color=RED_B
        ).to_edge(DOWN, buff=0.5)
        self.play(Write(barrier))
        self.wait(2.5)

        self.play(FadeOut(VGroup(title, left_grp, right_grp, vs, barrier)))
