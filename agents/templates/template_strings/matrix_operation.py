"""Matrix operation scene template — matrix math visualization"""

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

        # Matrix A
        matrix_a_data = {matrix_a}
        matrix_a = Matrix(
            matrix_a_data,
            left_bracket="[",
            right_bracket="]",
            element_to_mobject_config={{"font_size": 32}}
        )
        matrix_a.set_color(BLUE)

        # Operation symbol
        operation = "{operation}"
        if operation == "multiply":
            op_symbol = MathTex(r"\\times", font_size=40, color=WHITE)
        elif operation == "add":
            op_symbol = MathTex(r"+", font_size=40, color=WHITE)
        elif operation == "determinant":
            op_symbol = MathTex(r"\\det", font_size=32, color=WHITE)
        else:
            op_symbol = MathTex(r"=", font_size=40, color=WHITE)

        # Matrix B (if applicable)
        matrix_b_data = {matrix_b}
        if matrix_b_data:
            matrix_b = Matrix(
                matrix_b_data,
                left_bracket="[",
                right_bracket="]",
                element_to_mobject_config={{"font_size": 32}}
            )
            matrix_b.set_color(GREEN)

            equals = MathTex(r"=", font_size=40, color=WHITE)

            # Result matrix
            result_data = {result_matrix}
            result_matrix = Matrix(
                result_data,
                left_bracket="[",
                right_bracket="]",
                element_to_mobject_config={{"font_size": 32}}
            )
            result_matrix.set_color(YELLOW)

            # Arrange matrices
            equation = VGroup(matrix_a, op_symbol, matrix_b, equals, result_matrix)
            equation.arrange(RIGHT, buff=0.4)
        else:
            equals = MathTex(r"=", font_size=40, color=WHITE)
            result_val = MathTex(r"{scalar_result}", font_size=40, color=YELLOW)
            equation = VGroup(op_symbol, matrix_a, equals, result_val)
            equation.arrange(RIGHT, buff=0.3)

        equation.move_to(ORIGIN)

        # Scale if needed
        if equation.get_width() > 12:
            equation.scale_to_fit_width(11.5)

        # Animate matrix appearance
        self.play(Write(matrix_a), run_time=1.0)
        self.play(Write(op_symbol), run_time=0.3)

        if matrix_b_data:
            self.play(Write(matrix_b), run_time=1.0)
            self.play(Write(equals), run_time=0.3)

            # Highlight row-column multiplication
            for i in range(len(matrix_a_data)):
                row = VGroup(*matrix_a.get_rows()[i])
                col = VGroup(*matrix_b.get_columns()[min(i, len(matrix_b_data[0])-1)])
                self.play(
                    row.animate.set_color(YELLOW),
                    col.animate.set_color(YELLOW),
                    run_time=0.3
                )
                self.play(
                    row.animate.set_color(BLUE),
                    col.animate.set_color(GREEN),
                    run_time=0.2
                )

            self.play(Write(result_matrix), run_time=1.0)
        else:
            self.play(Write(equals), Write(result_val), run_time=0.5)

        # Final highlight
        self.play(
            Circumscribe(equation, color="#e0af68", time_width=2),
            run_time=1.0
        )

        self.wait(3)
'''
