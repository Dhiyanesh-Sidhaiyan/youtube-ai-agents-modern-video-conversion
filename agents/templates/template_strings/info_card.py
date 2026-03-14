"""Info card scene template — information card grid"""

TEMPLATE = '''from manim import *

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
'''
