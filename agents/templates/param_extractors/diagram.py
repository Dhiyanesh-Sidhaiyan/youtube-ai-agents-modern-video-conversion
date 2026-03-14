"""Parameter extractor for diagram template"""
from agents.templates.utils import call_ollama_json

def extract_diagram_params(scene: dict) -> dict:
    """Extract parameters for diagram template."""
    prompt = f"""Extract a central concept and connected items from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- center_node: the central concept (max 15 chars)
- connected_nodes: array of 4-6 related concepts (max 15 chars each)

JSON:"""

    params = call_ollama_json(prompt)

    center = params.get("center_node", scene['title'][:15])
    connected = params.get("connected_nodes", ["Feature 1", "Feature 2", "Feature 3", "Feature 4"])

    connected = [str(n)[:15] for n in connected[:6]]

    return {
        "center_node": str(center)[:15],
        "connected_nodes": repr(connected)
    }
