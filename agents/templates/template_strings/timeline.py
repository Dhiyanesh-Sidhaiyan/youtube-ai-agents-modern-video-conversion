"""Timeline scene template — chronological event timeline"""

TEMPLATE = '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # Dark background
        bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # Title
        title = Text("{title}", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Timeline line
        timeline = Line(LEFT * 5.5, RIGHT * 5.5, color=WHITE, stroke_width=3)
        timeline.move_to(ORIGIN)

        self.play(Create(timeline), run_time=0.8)

        # Timeline events
        events = {timeline_events}
        colors = [BLUE_D, GREEN_D, ORANGE, PURPLE_B, TEAL_D]
        n_events = len(events)

        dots = VGroup()
        labels = VGroup()
        connectors = VGroup()

        for i, (year, event) in enumerate(events):
            x_pos = -5 + (i * 10 / max(n_events - 1, 1))
            color = colors[i % len(colors)]

            # Pulsing dot
            dot = Dot(point=[x_pos, 0, 0], radius=0.15, color=color)
            dot_glow = Dot(point=[x_pos, 0, 0], radius=0.25, color=color, fill_opacity=0.3)

            # Year label
            year_label = Text(str(year)[:10], font_size=16, color=color, weight=BOLD)
            year_label.next_to(dot, UP, buff=0.2)

            # Event label (alternating top/bottom)
            event_label = Text(str(event)[:20], font_size=14, color=WHITE)
            if i % 2 == 0:
                event_label.next_to(year_label, UP, buff=0.15)
            else:
                event_label.next_to(dot, DOWN, buff=0.35)

            dots.add(VGroup(dot_glow, dot))
            labels.add(VGroup(year_label, event_label))

        # Animate timeline events appearing
        for i, (dot_grp, label_grp) in enumerate(zip(dots, labels)):
            self.play(
                GrowFromCenter(dot_grp),
                FadeIn(label_grp, shift=DOWN * 0.2 if i % 2 == 0 else UP * 0.2),
                run_time=0.5
            )
            self.wait(0.2)

        # Progress line sweep
        progress = Line(LEFT * 5.5, LEFT * 5.5, color=YELLOW, stroke_width=5)
        progress.move_to(timeline)
        self.play(progress.animate.put_start_and_end_on(LEFT * 5.5, RIGHT * 5.5), run_time=1.5)

        self.wait(3)
'''
