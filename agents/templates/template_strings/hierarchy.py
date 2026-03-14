"""Hierarchy scene template — tree/hierarchical structure"""

TEMPLATE = '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#0f0f23", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Hierarchy data: [root, [child1, child2, ...]]
        root_label = "{root_node}"
        children = {child_nodes}

        # Root node at top
        root_text = Text(root_label[:20], font_size=24, color=WHITE, weight=BOLD)
        root_box = RoundedRectangle(
            corner_radius=0.15,
            width=root_text.get_width() + 0.6,
            height=0.8,
            color=BLUE, fill_opacity=0.3, stroke_width=3
        )
        root = VGroup(root_box, root_text).move_to(UP * 1.8)

        self.play(GrowFromCenter(root), run_time=0.6)

        # Child nodes
        n_children = min(len(children), 5)
        child_nodes_grp = VGroup()
        arrows = VGroup()

        total_width = (n_children - 1) * 2.5
        start_x = -total_width / 2

        for i, child_label in enumerate(children[:n_children]):
            x_pos = start_x + i * 2.5
            color = [GREEN_D, ORANGE, PURPLE_B, RED_D, TEAL_D][i % 5]

            child_text = Text(str(child_label)[:12], font_size=18, color=WHITE)
            child_box = RoundedRectangle(
                corner_radius=0.1,
                width=max(child_text.get_width() + 0.4, 1.5),
                height=0.6,
                color=color, fill_opacity=0.2, stroke_width=2
            )
            child = VGroup(child_box, child_text).move_to([x_pos, -0.5, 0])
            child_nodes_grp.add(child)

            # Arrow from root to child
            arrow = Arrow(
                root_box.get_bottom(),
                child_box.get_top(),
                color=GREY_B, stroke_width=2,
                buff=0.1
            )
            arrows.add(arrow)

        # Scale to fit
        all_elements = VGroup(root, child_nodes_grp, arrows)
        if all_elements.get_width() > 11:
            all_elements.scale_to_fit_width(10.5)
        all_elements.move_to(ORIGIN + DOWN * 0.3)

        # Animate children appearing
        for arrow, child in zip(arrows, child_nodes_grp):
            self.play(
                GrowArrow(arrow),
                FadeIn(child, shift=UP * 0.3),
                run_time=0.4
            )

        # Highlight root
        self.play(Indicate(root, color=YELLOW, scale_factor=1.05), run_time=0.5)
        self.wait(3)
'''
