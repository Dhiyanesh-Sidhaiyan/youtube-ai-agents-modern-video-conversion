"""
Animation Fixer Agent
Takes visual analysis results and regenerates scenes with specific fixes.
Uses fix instructions to modify Manim code and re-render.
"""

import json
import os
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
FIXER_MODEL = "phi4"
OLLAMA_TIMEOUT = 300


# Fix templates for common issues
FIX_TEMPLATES = {
    "positioning": """
# FIX: Scale down and center elements to avoid edge cutoff
.scale(0.85)
.move_to(ORIGIN)
# Use buff parameter for edge positioning:
.to_edge(UP, buff=0.5)  # Keep 0.5 units from edge
""",

    "animation_content": """
# FIX: Add more animation content and wait times
self.wait(1)  # Pause to let viewer absorb content
# Add transitions between elements:
self.play(FadeIn(element), run_time=0.5)
self.wait(0.5)
""",

    "colors": """
# FIX: Improve color contrast
# Use high-contrast color pairs:
title = Text("Title", color=WHITE)  # White on dark background
# Or with background:
text = Text("Content", color=BLUE_D).set_background_color(WHITE, opacity=0.8)
""",

    "content_density": """
# FIX: Add more visual elements
# Add supporting graphics:
box = RoundedRectangle(width=8, height=2, color=BLUE, fill_opacity=0.2)
# Add bullet points:
bullets = VGroup(*[Text(f"• Point {i}", font_size=24) for i in range(3)])
bullets.arrange(DOWN, aligned_edge=LEFT)
""",

    "alignment": """
# FIX: Proper alignment
# Center elements:
group.move_to(ORIGIN)
# Align multiple elements:
elements.arrange(DOWN, center=True, buff=0.3)
# Use aligned_edge for consistent alignment:
texts.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
""",

    "font": """
# FIX: Font size and readability
# Use readable font sizes:
title = Text("Title", font_size=44)  # Large for titles
body = Text("Content", font_size=28)  # Medium for body
small = Text("Note", font_size=20)  # Small for annotations
# Ensure contrast:
text = Text("Content", color=WHITE, weight=BOLD)
""",
}


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

Return ONLY the fixed Python code, no explanation."""


def read_scene_code(scene_file: str) -> str:
    """Read the original scene code."""
    if os.path.exists(scene_file):
        with open(scene_file, 'r') as f:
            return f.read()
    return ""


def call_ollama_fixer(prompt: str) -> str:
    """Call Ollama to fix the code."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": FIXER_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 2048}
            },
            timeout=OLLAMA_TIMEOUT
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"    Fixer LLM error: {e}")
        return ""


def extract_code(text: str) -> str:
    """Extract Python code from LLM response."""
    # Remove markdown code fences
    text = re.sub(r"```python\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


def apply_manual_fixes(code: str, fixes: list) -> str:
    """Apply rule-based fixes that don't need LLM."""
    fixed_code = code

    for fix in fixes:
        fix_type = fix.get("type", "")

        if fix_type == "positioning":
            # Add scale and centering
            # Find class definition and add scale to main elements
            if ".to_edge(" in fixed_code and "buff=" not in fixed_code:
                fixed_code = re.sub(
                    r'\.to_edge\((\w+)\)',
                    r'.to_edge(\1, buff=0.5)',
                    fixed_code
                )

        if fix_type == "animation_content":
            # Ensure wait calls exist
            if "self.wait(" not in fixed_code:
                # Add wait at end of construct
                fixed_code = re.sub(
                    r'(\s+)(self\.play\([^)]+\))(\s*$)',
                    r'\1\2\1self.wait(2)\3',
                    fixed_code,
                    flags=re.MULTILINE
                )

        if fix_type == "font":
            # Ensure font sizes are reasonable
            # Replace very small fonts
            fixed_code = re.sub(
                r'font_size=(\d+)',
                lambda m: f'font_size={max(20, int(m.group(1)))}',
                fixed_code
            )

    return fixed_code


def fix_scene(
    scene_id: int,
    scene_file: str,
    fix_instructions: dict,
    scenes_dir: str
) -> str:
    """Fix a scene based on visual analysis results."""
    print(f"    Fixing scene {scene_id}...")

    # Read original code
    original_code = read_scene_code(scene_file)
    if not original_code:
        print(f"    Could not read scene file: {scene_file}")
        return None

    class_name = f"Scene{scene_id}"
    fixes = fix_instructions.get("fixes", [])

    if not fixes:
        print(f"    No fixes needed")
        return None

    # Format issues and fix instructions
    issues_text = "\n".join([
        f"- {fix['type']}: {fix['description']}"
        for fix in fixes
    ])

    fix_instr_text = "\n".join([
        f"- {fix['manim_suggestion']}"
        for fix in fixes
    ])

    # Get relevant fix templates
    relevant_templates = []
    for fix in fixes:
        fix_type = fix.get("type", "")
        if fix_type in FIX_TEMPLATES:
            relevant_templates.append(f"## {fix_type}:\n{FIX_TEMPLATES[fix_type]}")

    templates_text = "\n\n".join(relevant_templates) if relevant_templates else "None"

    # First try manual fixes
    fixed_code = apply_manual_fixes(original_code, fixes)

    # If significant issues, use LLM
    critical_fixes = [f for f in fixes if f.get("type") in ["positioning", "animation_content"]]

    if critical_fixes:
        prompt = FIXER_PROMPT.format(
            original_code=original_code,
            issues=issues_text,
            fix_instructions=fix_instr_text,
            fix_templates=templates_text,
            class_name=class_name,
        )

        llm_response = call_ollama_fixer(prompt)
        if llm_response:
            llm_code = extract_code(llm_response)
            if llm_code and "class" in llm_code and "construct" in llm_code:
                fixed_code = llm_code

    # Ensure imports
    if "from manim import" not in fixed_code:
        fixed_code = "from manim import *\n\n" + fixed_code

    # Write fixed code
    fixed_file = os.path.join(scenes_dir, f"scene_{scene_id}_fixed.py")
    with open(fixed_file, 'w') as f:
        f.write(fixed_code)

    print(f"    Fixed code saved: {fixed_file}")
    return fixed_file


def fix_all_scenes(
    scene_results: list,
    visual_analysis: dict,
    scenes_dir: str
) -> list:
    """Fix all scenes that need improvement."""
    print("\n[Animation Fixer] Fixing low-quality scenes...")

    fix_instructions_map = {
        instr["scene_id"]: instr
        for instr in visual_analysis.get("fix_instructions", [])
    }

    fixed_results = []

    for scene in scene_results:
        scene_id = scene["scene_id"]

        if scene_id in fix_instructions_map:
            instr = fix_instructions_map[scene_id]
            scene_file = os.path.join(scenes_dir, f"scene_{scene_id}.py")

            fixed_file = fix_scene(scene_id, scene_file, instr, scenes_dir)

            if fixed_file:
                # Re-render the fixed scene
                from agents.animation_agent import render_manim, _find_rendered_mp4

                class_name = f"Scene{scene_id}"
                success, err = render_manim(
                    fixed_file, class_name, os.path.dirname(scenes_dir)
                )

                if success:
                    mp4 = _find_rendered_mp4(class_name, os.path.dirname(scenes_dir))
                    if mp4:
                        print(f"    Scene {scene_id} re-rendered: {mp4}")
                        fixed_results.append({
                            **scene,
                            "mp4_path": mp4,
                            "fixed": True,
                        })
                        continue
                else:
                    print(f"    Re-render failed: {err[-100:]}")

        # Keep original
        fixed_results.append({**scene, "fixed": False})

    fixed_count = sum(1 for r in fixed_results if r.get("fixed"))
    print(f"\n[Animation Fixer] Fixed {fixed_count} scenes")

    return fixed_results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python animation_fixer.py <scene_results.json> <visual_analysis.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        scene_results = json.load(f)
    with open(sys.argv[2]) as f:
        visual_analysis = json.load(f)

    scenes_dir = "output/scenes"
    fix_all_scenes(scene_results, visual_analysis, scenes_dir)
