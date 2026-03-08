from manim import *

class Scene6(Scene):
    def construct(self):
        # Dark background for better visibility
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title with animation
        title = Text("Building LLM Applications", font_size=40, color=WHITE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(DrawBorderThenFill(title), run_time=0.8)
        self.wait(0.3)

        # Process steps with enhanced styling
        step_data = [
            ['Punch Cards', 'Early computing used punch cards'],
            ['Assembly Langs', 'Low-level programming language'],
            ['High-Level Lang', 'Languages such as Python and Java'],
            ['LLMs Emergence', 'Large Language Models (LLMs) rise']
        ]
        colors = [BLUE_D, GREEN_D, ORANGE, PURPLE_B]

        steps = VGroup()
        step_numbers = VGroup()

        for i, (step_title, step_desc) in enumerate(step_data):
            color = colors[i % len(colors)]

            # Step box with gradient feel
            box = RoundedRectangle(
                corner_radius=0.2, width=2.4, height=1.4,
                color=color, fill_opacity=0.2, stroke_width=3
            )

            # Step number badge
            num_circle = Circle(radius=0.25, color=color, fill_opacity=1)
            num_text = Text(str(i + 1), font_size=20, color=WHITE, weight=BOLD)
            num_badge = VGroup(num_circle, num_text)

            # Step title
            txt = Text(step_title, font_size=16, color=WHITE, weight=BOLD)
            txt.move_to(box.get_center())

            step_group = VGroup(box, txt)
            steps.add(step_group)
            step_numbers.add(num_badge)

        steps.arrange(RIGHT, buff=0.5).move_to(ORIGIN + DOWN * 0.1)

        # Position number badges above boxes
        for i, (step, badge) in enumerate(zip(steps, step_numbers)):
            badge.next_to(step, UP, buff=0.15)

        # Animate steps appearing one by one
        for i, (step, badge) in enumerate(zip(steps, step_numbers)):
            self.play(
                GrowFromCenter(badge),
                DrawBorderThenFill(step[0]),
                FadeIn(step[1]),
                run_time=0.5
            )
            self.wait(0.2)

        # Animated arrows with pulse effect
        arrows = VGroup()
        for i in range(len(steps) - 1):
            arr = Arrow(
                steps[i].get_right() + RIGHT * 0.1,
                steps[i + 1].get_left() + LEFT * 0.1,
                buff=0.05, color=YELLOW, stroke_width=4,
                max_tip_length_to_length_ratio=0.3
            )
            arrows.add(arr)

        self.play(
            LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2),
            run_time=0.8
        )
        self.wait(0.5)

        # Flash through the process
        for i, step in enumerate(steps):
            self.play(
                Flash(step, color=colors[i % len(colors)], line_length=0.3),
                run_time=0.3
            )

        # Hold final frame for freeze (no fade out)
        self.wait(3)