"""Parameter extractor for decision tree template"""
from agents.templates.utils import call_ollama_json

def extract_decision_tree_params(scene: dict) -> dict:
    """Extract parameters for decision tree template."""
    prompt = f"""Extract process steps from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- steps: array of [step_title, step_description] pairs
  (3-5 steps, titles max 25 chars)

JSON:"""

    params = call_ollama_json(prompt)

    steps = params.get("steps", [
        ["Step 1", "First action"],
        ["Step 2", "Second action"],
        ["Step 3", "Final action"]
    ])

    # Ensure proper format
    formatted_steps = []
    for s in steps[:5]:
        if isinstance(s, (list, tuple)) and len(s) >= 2:
            formatted_steps.append([str(s[0])[:25], str(s[1])[:40]])
        elif isinstance(s, str):
            formatted_steps.append([str(s)[:25], ""])

    if not formatted_steps:
        formatted_steps = [["Start", ""], ["Process", ""], ["End", ""]]

    return {
        "steps_data": repr(formatted_steps)
    }


# ─── Main Generator ─────────────────────────────────────────────────────────
