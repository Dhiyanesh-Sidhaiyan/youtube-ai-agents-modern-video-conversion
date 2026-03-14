"""Parameter extractor for geometric theorem template"""
from agents.templates.utils import call_ollama_json

def extract_geometric_theorem_params(scene: dict) -> dict:
    """Extract parameters for geometric theorem template."""
    prompt = f"""Extract geometric theorem parameters from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- theorem_latex: The main theorem formula in LaTeX (e.g., "a^2 + b^2 = c^2")
- shape_type: one of "triangle", "circle", or "polygon"
- vertices: array of [x, y, 0] coordinates for shape vertices (e.g., [[0, 0, 0], [3, 0, 0], [3, 2, 0]])
- side_labels: array of [[x, y, 0], "label"] for labeling sides (e.g., [[[1.5, -0.3, 0], "a"], [[3.3, 1, 0], "b"]])
- proof_steps: array of LaTeX proof steps (e.g., ["a^2 = 9", "b^2 = 16", "c^2 = a^2 + b^2 = 25"])

JSON:"""

    params = call_ollama_json(prompt)

    theorem_latex = params.get("theorem_latex", "a^2 + b^2 = c^2")
    shape_type = params.get("shape_type", "triangle")
    vertices = params.get("vertices", [[0, 0, 0], [3, 0, 0], [0, 2, 0]])
    side_labels = params.get("side_labels", [
        [[1.5, -0.3, 0], "a"],
        [[-0.3, 1, 0], "b"],
        [[1.8, 1.2, 0], "c"]
    ])
    proof_steps = params.get("proof_steps", [
        "a = 3",
        "b = 4",
        "c = \\sqrt{a^2 + b^2} = 5"
    ])

    # Validate shape_type
    if shape_type not in ["triangle", "circle", "polygon"]:
        shape_type = "triangle"

    # Clean theorem latex
    theorem_latex = theorem_latex.replace('"', '').replace("'", "")
    if '\\\\' not in theorem_latex:
        theorem_latex = theorem_latex.replace('\\', '\\\\')

    # Clean proof steps
    clean_proof = []
    for step in proof_steps[:5]:
        step_str = str(step).replace('"', '').replace("'", "")
        if '\\\\' not in step_str:
            step_str = step_str.replace('\\', '\\\\')
        clean_proof.append(step_str)

    return {
        "theorem_latex": theorem_latex,
        "shape_type": shape_type,
        "vertices": repr(vertices),
        "side_labels": repr(side_labels),
        "proof_steps": repr(clean_proof)
    }
