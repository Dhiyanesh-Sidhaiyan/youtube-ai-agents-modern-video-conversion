"""Parameter extractor for graph visualization template"""
from agents.templates.utils import call_ollama_json

def extract_graph_visualization_params(scene: dict) -> dict:
    """Extract parameters for graph visualization template."""
    prompt = f"""Extract function graph parameters from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- function_latex: LaTeX representation of the function (e.g., "f(x) = x^2 - 2x + 1")
- function_code: Python lambda code for the function (e.g., "x**2 - 2*x + 1")
- x_range: [min, max, step] for x-axis (e.g., [-5, 5, 1])
- y_range: [min, max, step] for y-axis (e.g., [-2, 10, 1])
- x_label: x-axis label (e.g., "x")
- y_label: y-axis label (e.g., "y")
- key_points: array of [x, y, "label"] for important points (e.g., [[1, 0, "(1, 0)"]])

JSON:"""

    params = call_ollama_json(prompt)

    function_latex = params.get("function_latex", "f(x) = x^2")
    function_code = params.get("function_code", "x**2")
    x_range = params.get("x_range", [-5, 5, 1])
    y_range = params.get("y_range", [-2, 10, 1])
    x_label = params.get("x_label", "x")
    y_label = params.get("y_label", "y")
    key_points = params.get("key_points", [[0, 0, "(0, 0)"]])

    # Clean and validate
    function_latex = function_latex.replace('"', '').replace("'", "")[:50]
    function_code = function_code.replace('"', '').replace("'", "")[:50]

    # Ensure ranges are valid
    if not isinstance(x_range, list) or len(x_range) != 3:
        x_range = [-5, 5, 1]
    if not isinstance(y_range, list) or len(y_range) != 3:
        y_range = [-2, 10, 1]

    # Validate key_points format
    valid_points = []
    for pt in key_points[:4]:
        if isinstance(pt, (list, tuple)) and len(pt) >= 3:
            try:
                x, y = float(pt[0]), float(pt[1])
                label = str(pt[2])[:15]
                valid_points.append([x, y, label])
            except (ValueError, TypeError):
                pass

    if not valid_points:
        valid_points = [[0, 0, "(0, 0)"]]

    return {
        "function_latex": function_latex,
        "function_code": function_code,
        "x_range": repr(x_range),
        "y_range": repr(y_range),
        "x_label": x_label,
        "y_label": y_label,
        "key_points": repr(valid_points)
    }
