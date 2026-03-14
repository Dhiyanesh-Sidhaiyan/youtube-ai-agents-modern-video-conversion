"""Visual explanation scene template — annotated diagram"""

TEMPLATE = '''from manim import *

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
'''
