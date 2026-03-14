"""Parameter extractor for hierarchy template"""
from agents.templates.utils import call_ollama_json

def extract_hierarchy_params(scene: dict) -> dict:
    """Extract parameters for hierarchy template."""
    prompt = f"""Extract a hierarchy structure from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- root_node: the top-level item (max 20 chars)
- child_nodes: array of 3-5 child items (max 12 chars each)

JSON:"""

    params = call_ollama_json(prompt)

    root = params.get("root_node", scene['title'][:20])
    children = params.get("child_nodes", ["Item 1", "Item 2", "Item 3"])

    children = [str(c)[:12] for c in children[:5]]

    return {
        "root_node": str(root)[:20],
        "child_nodes": repr(children)
    }


# ─── Claude-Style Template Parameter Extractors ─────────────────────────────
