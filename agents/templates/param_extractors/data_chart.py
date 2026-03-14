"""Parameter extractor for data chart template"""
from agents.templates.utils import call_ollama_json

def extract_data_chart_params(scene: dict) -> dict:
    """Extract parameters for data chart template."""
    prompt = f"""Extract data for a bar chart animation.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- values: array of 4-6 numbers (e.g., [45, 78, 32, 91, 56])
- labels: array of corresponding labels (max 8 chars each)

JSON:"""

    params = call_ollama_json(prompt)

    values = params.get("values", [65, 45, 80, 55, 70])[:6]
    labels = params.get("labels", ["A", "B", "C", "D", "E"])[:6]

    # Ensure values are numbers
    values = [int(v) if isinstance(v, (int, float)) else 50 for v in values]
    labels = [str(lbl)[:8] for lbl in labels]

    return {
        "chart_values": repr(values),
        "chart_labels": repr(labels)
    }
