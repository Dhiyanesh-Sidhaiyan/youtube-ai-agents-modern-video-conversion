"""
prompts/animation_prompts.py — LLM prompt templates for Manim animation generation.

Extracted from agents/animation_agent.py (WRITER_PROMPT, REVIEWER_PROMPT).
"""

WRITER_PROMPT = """You are a Manim Community Edition expert. Write a complete, self-contained
Manim scene class for the following visual description.

Rules:
- Use ONLY Manim Community Edition (manim) imports
- Class name must be exactly: Scene{scene_id}
- Use simple shapes: Text, Circle, Rectangle, Arrow, NumberPlane, VGroup
- Animations: Write, FadeIn, FadeOut, Create, Transform, MoveToTarget, GrowArrow
- Duration: self.wait() calls should total ~30 seconds of animation
- No external images or assets
- The code must run with: manim -pql scene_{scene_id}.py Scene{scene_id}

Visual description:
{visual_description}

Scene title: {title}

Return ONLY the Python code, no explanation, no markdown fences."""


REVIEWER_PROMPT = """Review this Manim Community Edition code for correctness.
Check for:
1. Correct imports (from manim import *)
2. Valid class name matching Scene{scene_id}
3. Valid Manim API calls (no hallucinated methods)
4. No syntax errors
5. Self-contained (no external files)

If the code is correct, reply with: APPROVED
If there are issues, reply with: FIX NEEDED
Then list the exact issues and provide the corrected full code.

Code to review:
{code}"""


FIXER_PROMPT = """You are a Manim code fixer. The following Manim scene has visual issues that need to be fixed.

ORIGINAL CODE:
```python
{original_code}
```

ISSUES DETECTED:
{issues}

FIX INSTRUCTIONS:
{fix_instructions}

REFERENCE FIXES:
{fix_templates}

Rewrite the Manim code with these fixes applied. Key rules:
1. Keep the same class name: {class_name}
2. Keep the same overall structure and content
3. Apply the specific fixes for each issue
4. Ensure all elements are properly positioned (not cut off at edges)
5. Use appropriate font sizes (title: 40-48, body: 24-32)
6. Add self.wait() calls between animations
7. Scale down large elements with .scale(0.85) if needed
8. IMPORTANT: For dark/contrast issues, ADD A BACKGROUND at the start of construct():
   bg = Rectangle(width=16, height=10, fill_color="#1a1a2e", fill_opacity=1, stroke_width=0)
   self.add(bg)
9. Use WHITE or bright colors (YELLOW, BLUE_A, GREEN_A) for text on dark backgrounds

Return ONLY the fixed Python code, no explanation."""
