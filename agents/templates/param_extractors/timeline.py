"""Parameter extractor for timeline template"""
from agents.templates.utils import call_ollama_json

def extract_timeline_params(scene: dict) -> dict:
    """Extract parameters for timeline template."""
    prompt = f"""Extract timeline events from this content.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- events: array of [year/label, event_description] pairs
  e.g., [["2020", "Event 1"], ["2021", "Event 2"], ...]
  (4-6 events, labels max 10 chars, events max 20 chars)

JSON:"""

    params = call_ollama_json(prompt)

    events = params.get("events", [
        ["Step 1", "First event"],
        ["Step 2", "Second event"],
        ["Step 3", "Third event"],
        ["Step 4", "Fourth event"]
    ])

    # Ensure proper format
    formatted_events = []
    for e in events[:6]:
        if isinstance(e, (list, tuple)) and len(e) >= 2:
            formatted_events.append([str(e[0])[:10], str(e[1])[:20]])
        elif isinstance(e, str):
            formatted_events.append([str(len(formatted_events)+1), str(e)[:20]])

    if not formatted_events:
        formatted_events = [["1", "Event 1"], ["2", "Event 2"], ["3", "Event 3"]]

    return {
        "timeline_events": repr(formatted_events)
    }
