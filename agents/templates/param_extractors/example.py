"""Parameter extractor for example template"""
from agents.templates.utils import call_ollama_json

def extract_example_params(scene: dict) -> dict:
    """Extract parameters for example template."""
    prompt = f"""Extract parameters for an example demonstration animation.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- example_content: the example text or code (max 60 chars)
- result_text: the result or output (max 40 chars)

JSON:"""

    params = call_ollama_json(prompt)

    return {
        "example_content": params.get("example_content", "Example content here")[:60],
        "result_text": params.get("result_text", "Result: Success")[:40]
    }
