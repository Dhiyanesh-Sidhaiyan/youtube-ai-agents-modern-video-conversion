from manim import *

class Scene4(Scene):
    def construct(self):
        title = Text("Framework Components", font_size=42, color=BLUE).to_edge(UP, buff=0.3)
        self.play(Write(title))
        self.wait(0.3)

        components = [
            ("Research Agent", "Analyzes abstract\nExtracts key concepts", BLUE, UL),
            ("Script Agent", "Structures into scenes\nNarration + visuals", GREEN, UR),
            ("TTS Engine", "21 Indian languages\nHigh-quality speech", ORANGE, DL),
            ("Video Creator", "Manim animations\nFinal MP4 output", PURPLE, DR),
        ]

        boxes = VGroup()
        positions = [UL * 2.8 + LEFT * 0.5, UR * 2.8 + RIGHT * 0.5,
                     DL * 2.8 + LEFT * 0.5, DR * 2.8 + RIGHT * 0.5]

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
