"""Equation derivation scene template — step-by-step math derivation"""

TEMPLATE = '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background optimized for math
        bg = Rectangle(width=16, height=10, fill_color="#0f0f1a", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=36, color="#7aa2f7", weight=BOLD)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=0.6)

        # Derivation steps - each step transforms into the next
        steps = {derivation_steps}

        # Color mapping for consistent variable highlighting
        color_map = {{
            "x": BLUE,
            "y": GREEN,
            "a": ORANGE,
            "b": YELLOW,
            "c": PURPLE,
            "=": WHITE,
        }}

        prev_eq = None
        step_group = VGroup()

        for i, (step_label, latex_eq) in enumerate(steps):
            # Step number
            step_num = Text(f"Step {{i+1}}:", font_size=20, color=GREY_B)

            # Equation with color mapping
            equation = MathTex(latex_eq, font_size=36, tex_to_color_map=color_map)

            # Group step label and equation
            step_row = VGroup(step_num, equation).arrange(RIGHT, buff=0.5)
            step_group.add(step_row)

        # Arrange all steps vertically
        step_group.arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        step_group.next_to(title, DOWN, buff=0.6)

        # Scale to fit if needed
        if step_group.get_width() > 12:
            step_group.scale_to_fit_width(11.5)
        if step_group.get_height() > 5.5:
            step_group.scale_to_fit_height(5)

        # Animate each step with transformation effect
        for i, step_row in enumerate(step_group):
            if i == 0:
                self.play(Write(step_row), run_time=1.0)
            else:
                # Show step label
                self.play(FadeIn(step_row[0]), run_time=0.3)
                # Transform from previous equation to current
                if i > 0:
                    prev_eq = step_group[i-1][1].copy()
                    self.play(
                        TransformMatchingTex(prev_eq, step_row[1]),
                        run_time=1.2
                    )
            self.wait(0.6)

        # Final highlight on the result
        final_eq = step_group[-1][1]
        result_box = SurroundingRectangle(
            final_eq, color="#e0af68", buff=0.15,
            corner_radius=0.1, stroke_width=2
        )
        self.play(Create(result_box), run_time=0.5)

        # Result label
        result_label = Text("Result", font_size=18, color="#e0af68")
        result_label.next_to(result_box, RIGHT, buff=0.3)
        self.play(FadeIn(result_label), run_time=0.3)

        self.wait(3)
'''
