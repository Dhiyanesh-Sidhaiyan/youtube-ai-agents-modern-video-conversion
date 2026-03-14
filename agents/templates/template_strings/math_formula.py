"""Math formula scene template — LaTeX equation display"""

TEMPLATE = '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#0f0f23", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Main equation with animated writing
        equation = MathTex(r"{equation}", font_size=48, color=WHITE)
        equation.move_to(ORIGIN + UP * 0.8)

        # Box around equation
        eq_box = SurroundingRectangle(
            equation, color=BLUE, buff=0.3,
            corner_radius=0.1, stroke_width=2
        )

        self.play(Write(equation), run_time=1.5)
        self.play(Create(eq_box), run_time=0.5)
        self.wait(0.5)

        # Explanation text
        explanation = Text("{explanation}", font_size=24, color=GREY_B)
        explanation.next_to(eq_box, DOWN, buff=0.6)

        # Scale if needed
        if explanation.get_width() > 11:
            explanation.scale_to_fit_width(10.5)

        self.play(FadeIn(explanation, shift=UP * 0.3), run_time=0.6)

        # Highlight parts of the equation
        self.play(Circumscribe(equation, color=YELLOW, time_width=2), run_time=1.0)
        self.wait(3)
'''
