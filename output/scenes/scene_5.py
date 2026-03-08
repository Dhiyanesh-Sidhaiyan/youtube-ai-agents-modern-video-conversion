from manim import *

class Scene5(Scene):
    def construct(self):
        # Create the split-screen background
        left_screen = Rectangle(width=4, height=3, color=BLUE_E).shift(LEFT * 2)
        right_screen = Rectangle(width=4, height=3, color=GREEN_E).shift(RIGHT * 2)

        self.play(Create(left_screen), Create(right_screen))
        
        # Title
        title = Text("Demonstrating the Framework's Application", font_size=48)
        title.to_edge(UP)
        self.play(FadeIn(title))

        # Left side: Educator creating a video with AI framework
        educator_label = Text("Educator Creating Video").scale(0.8).next_to(left_screen, UP)
        ai_framework_label = Text("AI Framework", color=YELLOW).scale(0.7).next_to(educator_label, DOWN)

        self.play(FadeIn(educator_label), FadeIn(ai_framework_label))

        # Draw a circle to represent the AI framework
        ai_circle = Circle(radius=0.5, color=YELLOW)
        ai_circle.move_to(ai_framework_label.get_center())
        
        self.play(Create(ai_circle))
        self.wait(3)

        # Right side: Students watching the final product in class
        students_label = Text("Students Watching Video").scale(0.8).next_to(right_screen, UP)
        video_frame = Rectangle(width=2, height=1.5, color=WHITE).move_to(right_screen.get_center())
        
        self.play(FadeIn(students_label), Create(video_frame))
        self.wait(3)

        # Animate the transition from creation to watching
        arrow = Arrow(start=ai_circle.get_right(), end=video_frame.get_left(), buff=0.2, color=RED)
        
        self.play(GrowArrow(arrow))
        self.wait(2)

        # Fade out all elements
        self.play(FadeOut(title), FadeOut(educator_label), FadeOut(ai_framework_label),
                  FadeOut(students_label), FadeOut(left_screen), FadeOut(right_screen),
                  FadeOut(video_frame), FadeOut(arrow))

        self.wait(5)