"""Intro scene template — animated title + bullet points"""

TEMPLATE = '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark blue gradient background for better visibility
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

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
'''
