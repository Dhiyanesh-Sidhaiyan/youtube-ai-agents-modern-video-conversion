"""Diagram scene template — flowchart or system diagram"""

TEMPLATE = '''from manim import *
import numpy as np

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#16213e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Central node
        center_text = Text("{center_node}", font_size=24, color=WHITE, weight=BOLD)
        center_circle = Circle(radius=0.8, color=BLUE, fill_opacity=0.3, stroke_width=3)
        center_node = VGroup(center_circle, center_text)
        center_node.move_to(ORIGIN)

        self.play(GrowFromCenter(center_node), run_time=0.7)

        # Connected nodes
        nodes_data = {connected_nodes}
        colors = [GREEN_D, ORANGE, PURPLE_B, RED_D, TEAL_D, YELLOW_D]
        n_nodes = len(nodes_data)

        nodes = VGroup()
        arrows = VGroup()

        for i, node_text in enumerate(nodes_data):
            angle = i * TAU / n_nodes - PI/2  # Start from top
            radius = 2.2
            pos = center_node.get_center() + radius * np.array([np.cos(angle), np.sin(angle), 0])
            color = colors[i % len(colors)]

            # Node
            node_label = Text(str(node_text)[:15], font_size=18, color=WHITE)
            node_box = RoundedRectangle(
                corner_radius=0.1,
                width=node_label.get_width() + 0.4,
                height=0.6,
                color=color, fill_opacity=0.2, stroke_width=2
            )
            node = VGroup(node_box, node_label).move_to(pos)
            nodes.add(node)

            # Curved arrow from center to node
            arrow = CurvedArrow(
                center_circle.get_edge_center(pos - center_node.get_center()),
                node_box.get_edge_center(center_node.get_center() - pos),
                color=color, stroke_width=2,
                angle=0.3 if i % 2 == 0 else -0.3
            )
            arrows.add(arrow)

        # Scale to fit
        all_elements = VGroup(center_node, nodes, arrows)
        if all_elements.get_width() > 11:
            all_elements.scale_to_fit_width(10.5)
        all_elements.move_to(ORIGIN + DOWN * 0.3)

        # Animate connections
        for node, arrow in zip(nodes, arrows):
            self.play(
                GrowArrow(arrow),
                FadeIn(node, scale=0.5),
                run_time=0.4
            )
            self.wait(0.1)

        # Pulse center
        self.play(
            Indicate(center_node, color=YELLOW, scale_factor=1.1),
            run_time=0.6
        )
        self.wait(3)
'''
