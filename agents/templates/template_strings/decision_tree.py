"""Decision tree scene template — branching decision flow"""

TEMPLATE = '''from manim import *

class Scene{scene_id}(Scene):
    def construct(self):
        # ═══ CLAUDE-STYLE COLORS ═══
        BG_DARK = "#1a1b26"
        BG_CARD = "#24283b"
        TEXT_PRIMARY = "#c0caf5"
        TEXT_HEADING = "#7aa2f7"
        BORDER_SUBTLE = "#3b4261"
        STEP_COLORS = ["#7aa2f7", "#9ece6a", "#e0af68", "#bb9af7", "#7dcfff"]
        ARROW_COLOR = "#565f89"

        # Background
        bg = Rectangle(width=16, height=10, fill_color=BG_DARK, fill_opacity=1, stroke_width=0)
        self.add(bg)

        # ═══ TITLE ═══
        title = Text("{title}", font_size=36, color=TEXT_HEADING, weight=BOLD)
        title.to_edge(UP, buff=0.4)

        self.play(Write(title), run_time=0.7)
        self.wait(0.2)

        # ═══ DECISION FLOW STEPS ═══
        steps_data = {steps_data}
        n_steps = len(steps_data)

        step_boxes = VGroup()
        step_arrows = VGroup()

        # Calculate vertical spacing
        total_height = 5.5
        step_height = 0.8
        gap = (total_height - n_steps * step_height) / max(n_steps - 1, 1)

        for i, (step_title, step_desc) in enumerate(steps_data):
            color = STEP_COLORS[i % len(STEP_COLORS)]

            # Step number badge
            badge = Circle(radius=0.25, fill_color=color, fill_opacity=1, stroke_width=0)
            badge_num = Text(str(i + 1), font_size=18, color=BG_DARK, weight=BOLD)
            badge_num.move_to(badge.get_center())
            badge_grp = VGroup(badge, badge_num)

            # Step box
            box = RoundedRectangle(
                corner_radius=0.1, width=8, height=step_height,
                fill_color=BG_CARD, fill_opacity=1,
                stroke_color=color, stroke_width=2
            )

            # Step text
            step_txt = Text(step_title[:30], font_size=20, color=TEXT_PRIMARY, weight=BOLD)
            step_txt.move_to(box.get_center())
            if step_txt.get_width() > 7.5:
                step_txt.scale_to_fit_width(7)

            # Position
            y_pos = 2.2 - i * (step_height + gap)
            box.move_to([0, y_pos, 0])
            step_txt.move_to(box.get_center())
            badge_grp.next_to(box, LEFT, buff=0.3)

            step_group = VGroup(badge_grp, box, step_txt)
            step_boxes.add(step_group)

            # Arrow to next step
            if i < n_steps - 1:
                arrow = Arrow(
                    box.get_bottom() + DOWN * 0.1,
                    box.get_bottom() + DOWN * gap * 0.7,
                    color=ARROW_COLOR, stroke_width=3,
                    max_tip_length_to_length_ratio=0.4
                )
                step_arrows.add(arrow)

        # Animate steps appearing
        for i, step in enumerate(step_boxes):
            self.play(
                GrowFromCenter(step[0]),  # Badge
                FadeIn(step[1]),          # Box
                Write(step[2]),           # Text
                run_time=0.5
            )
            if i < len(step_arrows):
                self.play(GrowArrow(step_arrows[i]), run_time=0.3)

        self.wait(3)
'''
