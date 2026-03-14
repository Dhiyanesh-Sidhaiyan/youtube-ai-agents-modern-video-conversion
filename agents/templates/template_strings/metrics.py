"""Metrics scene template — key metrics dashboard"""

TEMPLATE = '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Metrics data
        metrics = {metrics_data}
        colors = [BLUE_D, GREEN_D, ORANGE, PURPLE_B]

        metric_groups = VGroup()

        for i, (label, value, unit) in enumerate(metrics[:4]):
            color = colors[i % len(colors)]

            # Value tracker for animation
            tracker = ValueTracker(0)

            # Create decimal number
            number = DecimalNumber(
                0, num_decimal_places=0,
                font_size=48, color=color
            )
            number.add_updater(lambda m, t=tracker: m.set_value(t.get_value()))

            # Unit label
            unit_text = Text(str(unit)[:8], font_size=20, color=GREY_B)
            unit_text.next_to(number, RIGHT, buff=0.15)

            # Metric label
            label_text = Text(str(label)[:15], font_size=22, color=WHITE, weight=BOLD)

            # Group
            metric_grp = VGroup(number, unit_text, label_text)
            label_text.next_to(VGroup(number, unit_text), DOWN, buff=0.2)
            metric_groups.add(VGroup(metric_grp, tracker, value))

        # Arrange metrics in 2x2 grid
        positions = [UP * 0.8 + LEFT * 3, UP * 0.8 + RIGHT * 3,
                     DOWN * 1.2 + LEFT * 3, DOWN * 1.2 + RIGHT * 3]

        for mg, pos in zip(metric_groups, positions):
            mg[0].move_to(pos)

        # Add all metric displays
        for mg in metric_groups:
            self.add(mg[0])

        # Animate all counters simultaneously
        self.play(*[
            mg[1].animate.set_value(int(mg[2]))
            for mg in metric_groups
        ], run_time=2.0, rate_func=smooth)

        # Remove updaters and highlight
        for i, mg in enumerate(metric_groups):
            mg[0][0].clear_updaters()
            self.play(
                Flash(mg[0][0], color=colors[i], line_length=0.2),
                run_time=0.3
            )

        self.wait(3)
'''
