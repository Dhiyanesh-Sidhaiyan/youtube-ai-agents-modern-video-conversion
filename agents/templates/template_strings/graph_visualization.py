"""Graph visualization scene template — network/graph diagram"""

TEMPLATE = '''from manim import *
import numpy as np

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#0f0f1a", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=36, color="#7aa2f7", weight=BOLD)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=0.6)

        # Create axes
        axes = Axes(
            x_range={x_range},
            y_range={y_range},
            x_length=8,
            y_length=5,
            axis_config={{
                "color": GREY_B,
                "stroke_width": 2,
                "include_numbers": True,
                "font_size": 20,
            }},
            tips=True,
        )
        axes.shift(DOWN * 0.3)

        # Axis labels
        x_label = MathTex("{x_label}", font_size=24, color=WHITE)
        x_label.next_to(axes.x_axis, RIGHT, buff=0.2)
        y_label = MathTex("{y_label}", font_size=24, color=WHITE)
        y_label.next_to(axes.y_axis, UP, buff=0.2)

        self.play(Create(axes), run_time=1.0)
        self.play(Write(x_label), Write(y_label), run_time=0.4)

        # Function equation display
        func_eq = MathTex(r"{function_latex}", font_size=32, color=WHITE)
        func_eq.to_corner(UR, buff=0.5)
        eq_box = SurroundingRectangle(func_eq, color=BLUE, buff=0.15, corner_radius=0.1)

        self.play(Write(func_eq), Create(eq_box), run_time=0.6)

        # Plot the function
        graph = axes.plot(
            lambda x: {function_code},
            color=BLUE,
            stroke_width=3,
        )

        self.play(Create(graph), run_time=1.5)

        # Key points (roots, vertex, etc.)
        key_points = {key_points}

        for point_data in key_points:
            x, y, label = point_data[0], point_data[1], point_data[2]
            dot = Dot(axes.c2p(x, y), color=YELLOW, radius=0.1)
            dot_label = MathTex(label, font_size=20, color=YELLOW)
            dot_label.next_to(dot, UR, buff=0.15)

            self.play(
                GrowFromCenter(dot),
                Write(dot_label),
                run_time=0.5
            )

        self.wait(3)
'''
