"""
Pre-built Manim scenes for the YouTube AI Agent Framework educational video.
Each scene uses real Manim animations — shapes, arrows, diagrams, transitions.
These are used when the LLM-generated code fails all retry attempts.
"""

# Map scene_id → Manim Python source code
PREBUILT_SCENES: dict[int, str] = {}

# ─── Scene 1: The Challenge in Indian Higher Education ───────────────────────
PREBUILT_SCENES[1] = '''from manim import *

class Scene1(Scene):
    def construct(self):
        # Title
        title = Text("Indian Higher Education", font_size=44, color=BLUE).to_edge(UP, buff=0.4)
        self.play(Write(title))
        self.wait(0.5)

        # Stats box
        stat1 = Text("40 Million+", font_size=56, color=YELLOW)
        label1 = Text("Students Enrolled", font_size=28, color=WHITE)
        grp1 = VGroup(stat1, label1).arrange(DOWN, buff=0.15).move_to(LEFT * 3 + UP * 0.5)

        stat2 = Text("NEP 2020", font_size=48, color=GREEN)
        label2 = Text("Mandates Tech-Integrated Teaching", font_size=22, color=WHITE)
        grp2 = VGroup(stat2, label2).arrange(DOWN, buff=0.15).move_to(RIGHT * 2 + UP * 0.5)

        self.play(FadeIn(grp1, shift=UP))
        self.wait(0.4)
        self.play(FadeIn(grp2, shift=UP))
        self.wait(0.8)

        # Divider
        divider = Line(UP * 2, DOWN * 0.5, color=GREY).move_to(ORIGIN + UP * 0.5)
        self.play(Create(divider))

        # Problem bar
        problem = Rectangle(width=10, height=1.2, color=RED, fill_opacity=0.2)
        problem_text = Text(
            "Challenge: Educators lack tools to create multimedia content",
            font_size=22, color=RED_B
        )
        prob_grp = VGroup(problem, problem_text).arrange(DOWN, buff=0).move_to(DOWN * 2)
        self.play(FadeIn(prob_grp))
        self.wait(1)

        # Highlight NEP vs reality gap
        arrow = Arrow(grp2.get_bottom(), prob_grp.get_top(), color=ORANGE, buff=0.1)
        gap_label = Text("Gap ↓", font_size=26, color=ORANGE).next_to(arrow, RIGHT, buff=0.1)
        self.play(GrowArrow(arrow), Write(gap_label))
        self.wait(2)

        self.play(FadeOut(VGroup(title, grp1, grp2, divider, prob_grp, arrow, gap_label)))
'''

# ─── Scene 2: The Importance of Video-Based Learning ─────────────────────────
PREBUILT_SCENES[2] = '''from manim import *

class Scene2(Scene):
    def construct(self):
        title = Text("Video-Based Learning", font_size=44, color=BLUE).to_edge(UP, buff=0.4)
        self.play(Write(title))
        self.wait(0.4)

        # Left: Traditional teaching
        left_box = Rectangle(width=4.2, height=3.5, color=GREY, fill_opacity=0.15)
        left_label = Text("Traditional\\nTeaching", font_size=28, color=GREY_B)
        left_items = VGroup(
            Text("• Blackboard", font_size=22),
            Text("• One-way lecture", font_size=22),
            Text("• Limited reach", font_size=22),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        left_content = VGroup(left_label, left_items).arrange(DOWN, buff=0.3)
        left_grp = VGroup(left_box, left_content).move_to(LEFT * 2.8 + DOWN * 0.3)
        left_content.move_to(left_box.get_center())

        # Right: Video learning
        right_box = Rectangle(width=4.2, height=3.5, color=GREEN, fill_opacity=0.15)
        right_label = Text("Video Learning", font_size=28, color=GREEN_B)
        right_items = VGroup(
            Text("• Visual + Audio", font_size=22),
            Text("• Replayable anytime", font_size=22),
            Text("• Reaches millions", font_size=22),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        right_content = VGroup(right_label, right_items).arrange(DOWN, buff=0.3)
        right_grp = VGroup(right_box, right_content).move_to(RIGHT * 2.8 + DOWN * 0.3)
        right_content.move_to(right_box.get_center())

        vs = Text("VS", font_size=36, color=YELLOW).move_to(ORIGIN + DOWN * 0.3)

        self.play(FadeIn(left_grp, shift=LEFT * 0.5))
        self.play(Write(vs))
        self.play(FadeIn(right_grp, shift=RIGHT * 0.5))
        self.wait(0.8)

        # Highlight the barrier
        barrier = Text(
            "But: 90% of educators lack technical skills to produce video",
            font_size=22, color=RED_B
        ).to_edge(DOWN, buff=0.5)
        self.play(Write(barrier))
        self.wait(2.5)

        self.play(FadeOut(VGroup(title, left_grp, right_grp, vs, barrier)))
'''

# ─── Scene 3: Introducing the YouTube AI Agent Framework ─────────────────────
PREBUILT_SCENES[3] = '''from manim import *

class Scene3(Scene):
    def construct(self):
        title = Text("YouTube AI Agent Framework", font_size=40, color=BLUE).to_edge(UP, buff=0.4)
        self.play(Write(title))
        self.wait(0.5)

        # Input
        input_box = Rectangle(width=3, height=1, color=WHITE, fill_opacity=0.1)
        input_text = Text("Research Paper\\n/ Abstract", font_size=22)
        input_text.move_to(input_box.get_center())
        input_grp = VGroup(input_box, input_text).move_to(LEFT * 4 + UP * 0)

        # Output
        output_box = Rectangle(width=3, height=1, color=YELLOW, fill_opacity=0.2)
        output_text = Text("Educational\\nVideo (MP4)", font_size=22, color=YELLOW_B)
        output_text.move_to(output_box.get_center())
        output_grp = VGroup(output_box, output_text).move_to(RIGHT * 4 + UP * 0)

        self.play(FadeIn(input_grp))
        self.wait(0.3)

        # Four agents in a row
        agent_data = [
            ("Research\\n& Script", BLUE),
            ("Animation\\n(Manim)", GREEN),
            ("TTS\\nNarration", ORANGE),
            ("Video\\nAssembly", PURPLE),
        ]
        agents = VGroup()
        for label, color in agent_data:
            box = RoundedRectangle(corner_radius=0.2, width=2.2, height=1.3,
                                   color=color, fill_opacity=0.25)
            txt = Text(label, font_size=20, color=color)
            txt.move_to(box.get_center())
            agents.add(VGroup(box, txt))

        agents.arrange(RIGHT, buff=0.25).move_to(ORIGIN + DOWN * 0.2)
        self.play(FadeIn(agents, shift=UP * 0.3, lag_ratio=0.2))
        self.wait(0.4)

        # Arrows between agents
        arrows = VGroup()
        for i in range(len(agents) - 1):
            arr = Arrow(
                agents[i].get_right(), agents[i + 1].get_left(),
                buff=0.05, color=GREY_B, stroke_width=3
            )
            arrows.add(arr)
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2))

        # Input → first agent, last agent → output
        arr_in = Arrow(input_grp.get_right(), agents[0].get_left(),
                       buff=0.05, color=WHITE, stroke_width=3)
        arr_out = Arrow(agents[-1].get_right(), output_grp.get_left(),
                        buff=0.05, color=YELLOW, stroke_width=3)
        self.play(GrowArrow(arr_in), FadeIn(output_grp))
        self.play(GrowArrow(arr_out))
        self.wait(2.5)

        self.play(FadeOut(VGroup(title, input_grp, output_grp, agents, arrows, arr_in, arr_out)))
'''

# ─── Scene 4: Components of the AI Agent Framework ───────────────────────────
PREBUILT_SCENES[4] = '''from manim import *

class Scene4(Scene):
    def construct(self):
        title = Text("Framework Components", font_size=42, color=BLUE).to_edge(UP, buff=0.3)
        self.play(Write(title))
        self.wait(0.3)

        components = [
            ("Research Agent", "Analyzes abstract\\nExtracts key concepts", BLUE, UL),
            ("Script Agent", "Structures into scenes\\nNarration + visuals", GREEN, UR),
            ("TTS Engine", "21 Indian languages\\nHigh-quality speech", ORANGE, DL),
            ("Video Creator", "Manim animations\\nFinal MP4 output", PURPLE, DR),
        ]

        boxes = VGroup()
        positions = [
            LEFT * 3.3 + UP * 1.5,    # top-left (below title)
            RIGHT * 3.3 + UP * 1.5,   # top-right
            LEFT * 3.3 + DOWN * 1.5,  # bottom-left
            RIGHT * 3.3 + DOWN * 1.5  # bottom-right
        ]

        for i, (name, desc, color, _) in enumerate(components):
            box = RoundedRectangle(corner_radius=0.25, width=4.5, height=1.8,
                                   color=color, fill_opacity=0.2)
            name_t = Text(name, font_size=26, color=color, weight=BOLD)
            desc_t = Text(desc, font_size=19, color=WHITE)
            content = VGroup(name_t, desc_t).arrange(DOWN, buff=0.15)
            content.move_to(box.get_center())
            grp = VGroup(box, content).move_to(positions[i])
            boxes.add(grp)

        for box in boxes:
            self.play(FadeIn(box, scale=0.85), run_time=0.55)

        # Central hub
        hub = Circle(radius=0.55, color=YELLOW, fill_opacity=0.3)
        hub_label = Text("Pipeline", font_size=20, color=YELLOW)
        hub_label.move_to(hub.get_center())
        hub_grp = VGroup(hub, hub_label)
        self.play(FadeIn(hub_grp))

        # Arrows from hub to each box
        for box in boxes:
            arr = Arrow(hub_grp.get_center(), box.get_center(),
                        buff=0.6, color=YELLOW_A, stroke_width=2.5)
            self.play(GrowArrow(arr), run_time=0.35)

        self.wait(2.5)
        self.play(FadeOut(VGroup(title, boxes, hub_grp)))
'''

# ─── Scene 5: Demonstrating the Framework in Action ─────────────────────────
PREBUILT_SCENES[5] = '''from manim import *

class Scene5(Scene):
    def construct(self):
        title = Text("Framework in Action", font_size=42, color=BLUE).to_edge(UP, buff=0.3)
        self.play(Write(title))
        self.wait(0.3)

        # Pipeline steps as vertical flow
        steps = [
            ("Input: Python Programming Abstract", WHITE),
            ("Agent 1 → Script: 6 structured scenes", BLUE_B),
            ("Agent 2 → Manim animations per scene", GREEN_B),
            ("Agent 3 → Hindi/English narration WAVs", ORANGE),
            ("Agent 4 → Final MP4 video assembled", YELLOW_B),
        ]

        step_grps = VGroup()
        for i, (text, color) in enumerate(steps):
            circle = Circle(radius=0.28, color=color, fill_opacity=0.8)
            num = Text(str(i + 1), font_size=20, color=BLACK, weight=BOLD)
            num.move_to(circle.get_center())
            label = Text(text, font_size=22, color=color)
            row = VGroup(VGroup(circle, num), label).arrange(RIGHT, buff=0.35)
            step_grps.add(row)

        step_grps.arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to(DOWN * 0.4)

        for i, step in enumerate(step_grps):
            self.play(FadeIn(step, shift=RIGHT * 0.2), run_time=0.5)
            if i < len(step_grps) - 1:
                connector = Line(
                    step[0].get_bottom() + DOWN * 0.05,
                    step_grps[i + 1][0].get_top() + UP * 0.05,
                    color=GREY, stroke_width=2
                )
                self.play(Create(connector), run_time=0.25)
            self.wait(0.3)

        # Outcome callout
        outcome = Text(
            "Result: Professional video in minutes, not weeks",
            font_size=24, color=GREEN_B
        ).to_edge(DOWN, buff=0.45)
        box = SurroundingRectangle(outcome, color=GREEN, buff=0.15, corner_radius=0.1)
        self.play(Write(outcome), Create(box))
        self.wait(2.5)

        self.play(FadeOut(VGroup(title, step_grps, outcome, box)))
'''

# ─── Scene 6: Impact and Conclusion ──────────────────────────────────────────
PREBUILT_SCENES[6] = '''from manim import *

class Scene6(Scene):
    def construct(self):
        title = Text("Impact & Conclusion", font_size=44, color=BLUE).to_edge(UP, buff=0.3)
        self.play(Write(title))
        self.wait(0.4)

        # Impact metrics
        metrics = [
            ("40M+", "Students reached", GREEN),
            ("21", "Indian languages", ORANGE),
            ("100%", "Open Source", YELLOW),
            ("NEP 2020", "Aligned", BLUE),
        ]

        metric_grps = VGroup()
        for value, label, color in metrics:
            val_text = Text(value, font_size=52, color=color, weight=BOLD)
            lbl_text = Text(label, font_size=22, color=WHITE)
            grp = VGroup(val_text, lbl_text).arrange(DOWN, buff=0.15)
            box = SurroundingRectangle(grp, color=color, buff=0.25,
                                        corner_radius=0.15, fill_opacity=0.1)
            metric_grps.add(VGroup(box, grp))

        metric_grps.arrange_in_grid(2, 2, buff=0.5).move_to(ORIGIN + DOWN * 0.4)

        for m in metric_grps:
            self.play(FadeIn(m, scale=0.8), run_time=0.5)
        self.wait(0.6)

        # Final message
        finale = Text(
            "Empowering Every Educator Across India",
            font_size=28, color=YELLOW, weight=BOLD
        ).to_edge(DOWN, buff=0.5)
        underline = Line(finale.get_left(), finale.get_right(),
                         color=YELLOW, stroke_width=2).next_to(finale, DOWN, buff=0.05)
        self.play(Write(finale), Create(underline))
        self.wait(3)

        self.play(FadeOut(VGroup(title, metric_grps, finale, underline)))
'''
