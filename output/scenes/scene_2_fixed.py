from manim import *

class Scene2(Scene):
    def construct(self):
        # Title with drawing effect
        title = Text("Understanding Prompts as Executable Logic", font_size=40, color=BLUE, weight=BOLD).to_edge(UP, buff=0.5)
        self.play(DrawBorderThenFill(title), run_time=1.0)
        self.wait(0.3)

        # Central concept with glow effect
        concept_box = RoundedRectangle(
            corner_radius=0.3, width=9, height=2.2,
            color=GREEN, fill_opacity=0.15, stroke_width=3
        ).move_to(ORIGIN + UP * 0.3)

        # Add subtle glow
        glow = concept_box.copy().set_stroke(GREEN, width=8, opacity=0.3)

        concept_text = Text("Prompts as Executable Logic", font_size=34, color=GREEN, weight=BOLD)
        concept_text.move_to(concept_box.get_center())

        self.play(
            FadeIn(glow, scale=1.1),
            DrawBorderThenFill(concept_box),
            run_time=0.8
        )
        self.play(
            Write(concept_text),
            Circumscribe(concept_box, color=YELLOW, time_width=2),
            run_time=1.0
        )
        self.wait(0.5)

        # Supporting details with icons
        details = VGroup(
            Text("- Prompts guide LLMs with instructions.", font_size=22, color=WHITE),
            Text("- Outputs vary due to stochastic nature.", font_size=22, color=WHITE),
            Text("- Unlike deterministic software, prompts produce div", font_size=22, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(concept_box, DOWN, buff=0.6)

        # Animated entry with stagger
        self.play(
            LaggedStart(*[
                FadeIn(d, shift=LEFT * 0.3) for d in details
            ], lag_ratio=0.15),
            run_time=1.2
        )
        self.wait(2)

        # Highlight key concept and hold
        self.play(Indicate(concept_text, color=YELLOW, scale_factor=1.1))
        # Hold final frame for freeze (no fade out)
        self.wait(3)
