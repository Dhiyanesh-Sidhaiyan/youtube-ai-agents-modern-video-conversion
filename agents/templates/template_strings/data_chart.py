"""Data chart scene template — bar chart visualization"""

TEMPLATE = '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Animated bar chart
        values = {chart_values}
        labels = {chart_labels}
        colors = [BLUE_D, GREEN_D, ORANGE, PURPLE_B, RED_D, TEAL_D]

        max_val = max(values) if values else 1
        bars = VGroup()
        bar_labels = VGroup()
        value_texts = VGroup()

        for i, (val, label) in enumerate(zip(values, labels)):
            # Animated bar with gradient effect
            bar_height = (val / max_val) * 2.8
            bar = Rectangle(
                width=0.8, height=bar_height,
                fill_color=colors[i % len(colors)],
                fill_opacity=0.85,
                stroke_color=WHITE,
                stroke_width=1
            )
            bar.move_to(ORIGIN + LEFT * 3.5 + RIGHT * i * 1.2)
            bar.align_to(ORIGIN + DOWN * 1.5, DOWN)

            # Label below
            lbl = Text(str(label)[:8], font_size=16, color=WHITE)
            lbl.next_to(bar, DOWN, buff=0.15)

            # Value on top
            val_txt = Text(str(val), font_size=18, color=colors[i % len(colors)], weight=BOLD)
            val_txt.next_to(bar, UP, buff=0.1)

            bars.add(bar)
            bar_labels.add(lbl)
            value_texts.add(val_txt)

        # Scale to fit
        chart_group = VGroup(bars, bar_labels, value_texts)
        if chart_group.get_width() > 11:
            chart_group.scale_to_fit_width(10.5)
        chart_group.move_to(ORIGIN + DOWN * 0.3)

        # Animate bars growing from bottom
        for i, (bar, lbl, val) in enumerate(zip(bars, bar_labels, value_texts)):
            target_height = bar.height
            bar.stretch_to_fit_height(0.01)
            bar.align_to(ORIGIN + DOWN * 1.5, DOWN)
            self.play(
                bar.animate.stretch_to_fit_height(target_height).align_to(ORIGIN + DOWN * 1.5, DOWN),
                FadeIn(lbl),
                run_time=0.4
            )
            self.play(FadeIn(val, shift=DOWN * 0.2), run_time=0.2)

        # Highlight max value
        max_idx = values.index(max(values))
        self.play(
            Flash(bars[max_idx], color=YELLOW, line_length=0.3),
            Indicate(value_texts[max_idx], color=YELLOW, scale_factor=1.3),
            run_time=0.6
        )
        self.wait(3)
'''
