from manim import *

class Scene1(Scene):
    def construct(self):
        # Dark blue gradient background for better visibility
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Animated title with underline using high-contrast colors
        title = Text("Introduction to LLMs in Enterprises", font_size=44, color=WHITE, weight=BOLD).to_edge(UP, buff=0.5)
        underline = Line(
            title.get_left(), title.get_right(),
            color=YELLOW, stroke_width=3
        ).next_to(title, DOWN, buff=0.1)

        self.play(GrowFromCenter(title), run_time=0.8)
        self.play(Create(underline), run_time=0.4)
        self.wait(0.5)  # Added wait for better pacing

        # Subtitle with fade and shift using high-contrast colors
        subtitle = Text("Exploring LLMs in Healthcare, Finance, and Beyond", font_size=26, color=BLUE_A).next_to(underline, DOWN, buff=0.4)
        self.play(FadeIn(subtitle), run_time=0.5)
        self.wait(0.4)

        # Key points with staggered animation and icons using high-contrast colors
        points = VGroup(
            Text("* LLMs transform enterprise applications across indu", font_size=24, color=WHITE),
            Text("* Explore impacts on healthcare and finance sectors.", font_size=24, color=BLUE_A),
            Text("* Understand how neural networks drive innovation.", font_size=24, color=GREEN_A),
            Text("* Join Arsh from Adeline for insights.", font_size=24, color=YELLOW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(ORIGIN + DOWN * 1)

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