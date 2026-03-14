"""Parameter extractor for metrics template"""
from agents.templates.utils import call_ollama_json

def extract_metrics_params(scene: dict) -> dict:
    """Extract parameters for metrics template."""
    prompt = f"""Extract numeric metrics from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- metrics: array of [label, value, unit] tuples
  e.g., [["Users", 5000, "K"], ["Revenue", 120, "M"], ...]
  (3-4 metrics, labels max 15 chars, values as numbers, units max 8 chars)

JSON:"""

    params = call_ollama_json(prompt)

    metrics = params.get("metrics", [
        ["Metric 1", 100, "%"],
        ["Metric 2", 250, "K"],
        ["Metric 3", 50, "M"]
    ])

    # Ensure proper format
    formatted = []
    for m in metrics[:4]:
        if isinstance(m, (list, tuple)) and len(m) >= 3:
            formatted.append([str(m[0])[:15], int(m[1]) if isinstance(m[1], (int, float)) else 100, str(m[2])[:8]])
        elif isinstance(m, (list, tuple)) and len(m) >= 2:
            formatted.append([str(m[0])[:15], int(m[1]) if isinstance(m[1], (int, float)) else 100, ""])

    if not formatted:
        formatted = [["Value 1", 100, "%"], ["Value 2", 200, "K"], ["Value 3", 50, "M"]]

    return {
        "metrics_data": repr(formatted)
    }
