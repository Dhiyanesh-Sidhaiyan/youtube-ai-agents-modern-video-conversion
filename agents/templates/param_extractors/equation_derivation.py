"""Parameter extractor for equation derivation template"""
from agents.templates.utils import call_ollama_json

def extract_equation_derivation_params(scene: dict) -> dict:
    """Extract parameters for equation derivation template."""
    prompt = f"""Extract step-by-step equation derivation from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- steps: array of [step_label, latex_equation] pairs showing the derivation
  e.g., [["Original", "ax^2 + bx + c = 0"], ["Divide by a", "x^2 + \\\\frac{{b}}{{a}}x = -\\\\frac{{c}}{{a}}"], ...]
  (3-5 steps, each equation in valid LaTeX)

JSON:"""

    params = call_ollama_json(prompt)

    steps = params.get("steps", [
        ["Start", "ax + b = c"],
        ["Subtract b", "ax = c - b"],
        ["Divide by a", "x = \\frac{c - b}{a}"]
    ])

    # Validate and clean steps
    formatted_steps = []
    for step in steps[:5]:
        if isinstance(step, (list, tuple)) and len(step) >= 2:
            label = str(step[0])[:20]
            # Clean LaTeX - ensure proper escaping
            latex = str(step[1]).replace('"', '').replace("'", "")
            # Don't double-escape if already escaped
            if '\\\\' not in latex:
                latex = latex.replace('\\', '\\\\')
            formatted_steps.append([label, latex])

    if not formatted_steps:
        formatted_steps = [
            ["Start", "ax + b = c"],
            ["Isolate", "ax = c - b"],
            ["Solve", "x = \\\\frac{c - b}{a}"]
        ]

    return {
        "derivation_steps": repr(formatted_steps)
    }
