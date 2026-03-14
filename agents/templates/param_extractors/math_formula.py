"""Parameter extractor for math formula template"""
from agents.templates.utils import call_ollama_json

def extract_math_formula_params(scene: dict) -> dict:
    """Extract parameters for math formula template."""
    prompt = f"""Extract a mathematical equation from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- equation: LaTeX equation (e.g., "E = mc^2" or "\\\\frac{{a}}{{b}}")
- explanation: brief explanation of the equation (max 60 chars)

JSON:"""

    params = call_ollama_json(prompt)

    equation = params.get("equation", "y = mx + b")
    explanation = params.get("explanation", "A fundamental equation")

    # Clean equation for LaTeX
    equation = equation.replace("\\", "\\\\").replace('"', '')[:80]

    return {
        "equation": equation,
        "explanation": explanation[:60]
    }
