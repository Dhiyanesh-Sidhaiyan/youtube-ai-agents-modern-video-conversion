from manim import *

class Scene10(Scene):
    def construct(self):
        # Title with celebratory entry
        title = Text("The Future of LLMs in Enterprises", font_size=44, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(
            GrowFromCenter(title),
            Flash(title, color=BLUE, line_length=0.4, num_lines=12),
            run_time=1.0
        )
        self.wait(0.3)

        # Key takeaways header
        takeaway_header = Text("Key Takeaways", font_size=28, color=YELLOW)
        takeaway_header.next_to(title, DOWN, buff=0.5)
        header_line = Line(LEFT * 2, RIGHT * 2, color=YELLOW, stroke_width=2)
        header_line.next_to(takeaway_header, DOWN, buff=0.1)

        self.play(
            FadeIn(takeaway_header, shift=DOWN * 0.2),
            Create(header_line),
            run_time=0.5
        )

        # Key takeaways with checkmarks
        takeaways = VGroup(
            Text("1. LLMs provide powerful capabilities for enterp", font_size=26, color=WHITE),
            Text("2. Complexities arise with integrating LLMs into", font_size=26, color=WHITE),
            Text("3. Robust systems are essential for future stabi", font_size=26, color=WHITE),
            Text("4. Ensuring efficacy is key in new paradigms.", font_size=26, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).next_to(header_line, DOWN, buff=0.5)

        # Add checkmark icons
        for i, t in enumerate(takeaways):
            check = Text("✓", font_size=26, color=GREEN).next_to(t, LEFT, buff=0.2)
            self.play(
                GrowFromCenter(check),
                FadeIn(t, shift=RIGHT * 0.3),
                run_time=0.4
            )
            self.wait(0.15)

        self.wait(0.8)

        # Final message with dramatic reveal
        finale_box = RoundedRectangle(
            corner_radius=0.2, width=10, height=1.2,
            color=GOLD, fill_opacity=0.15, stroke_width=3
        ).to_edge(DOWN, buff=0.6)

        finale = Text(
            "Embrace innovation, build resilient and effective ",
            font_size=30, color=GOLD, weight=BOLD
        ).move_to(finale_box.get_center())

        # Stars decoration
        stars = VGroup(*[
            Star(n=5, color=YELLOW, fill_opacity=0.8).scale(0.15)
            for _ in range(6)
        ])
        stars.arrange(RIGHT, buff=0.4).next_to(finale_box, UP, buff=0.15)

        self.play(
            DrawBorderThenFill(finale_box),
            run_time=0.5
        )
        self.play(
            Write(finale),
            LaggedStart(*[
                SpinInFromNothing(star) for star in stars
            ], lag_ratio=0.1),
            run_time=1.0
        )

        # Celebration flash
        self.play(
            Circumscribe(finale, color=YELLOW, time_width=1.5),
            run_time=0.8
        )
        # Hold final frame for freeze (no fade out)
        self.wait(3)
