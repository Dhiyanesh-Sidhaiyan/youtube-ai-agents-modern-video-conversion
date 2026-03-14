"""Geometric theorem scene template — geometric shapes and proof"""

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

        # Theorem statement
        theorem = MathTex(r"{theorem_latex}", font_size=40, color=WHITE)
        theorem.next_to(title, DOWN, buff=0.5)
        self.play(Write(theorem), run_time=1.0)
        self.wait(0.5)

        # Create the geometric shape
        shape_type = "{shape_type}"
        shape_group = VGroup()

        if shape_type == "triangle":
            # Right triangle for Pythagorean theorem
            vertices = {vertices}
            triangle = Polygon(*[np.array(v) for v in vertices], color=BLUE, fill_opacity=0.3, stroke_width=3)
            shape_group.add(triangle)

            # Side labels
            labels = {side_labels}
            for label_data in labels:
                pos = np.array(label_data[0])
                text = label_data[1]
                label = MathTex(text, font_size=28, color=YELLOW)
                label.move_to(pos)
                shape_group.add(label)

            # Right angle marker if applicable
            shape_group.add(
                Square(side_length=0.3, color=WHITE, stroke_width=2)
                .move_to(np.array(vertices[1]) + np.array([0.15, 0.15, 0]))
            )

        elif shape_type == "circle":
            circle = Circle(radius=1.5, color=BLUE, stroke_width=3)
            shape_group.add(circle)

        elif shape_type == "polygon":
            vertices = {vertices}
            polygon = Polygon(*[np.array(v) for v in vertices], color=BLUE, fill_opacity=0.3, stroke_width=3)
            shape_group.add(polygon)

        # Position shape
        shape_group.move_to(DOWN * 0.8 + LEFT * 2)

        self.play(Create(shape_group), run_time=1.5)

        # Proof steps or explanations
        proof_steps = {proof_steps}
        proof_group = VGroup()

        for step in proof_steps:
            step_text = MathTex(step, font_size=24, color=WHITE)
            proof_group.add(step_text)

        proof_group.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        proof_group.move_to(DOWN * 0.8 + RIGHT * 2.5)

        for step_text in proof_group:
            self.play(Write(step_text), run_time=0.8)
            self.wait(0.3)

        # QED or conclusion highlight
        qed = Text("∎", font_size=36, color="#9ece6a")
        qed.next_to(proof_group, DOWN, buff=0.3)
        self.play(FadeIn(qed, scale=1.5), run_time=0.5)

        self.wait(3)
'''
