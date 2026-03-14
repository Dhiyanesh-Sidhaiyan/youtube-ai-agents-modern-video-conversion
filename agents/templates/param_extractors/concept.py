"""Parameter extractor for concept template"""
from agents.templates.utils import call_ollama_json

def extract_concept_params(scene: dict) -> dict:
    """Extract parameters for concept template."""
    prompt = f"""Extract parameters for a concept explanation animation.

Title: {scene['title']}
Visual Description: {scene.get('visual_description', '')}
Narration: {scene.get('narration_text', '')}

Return JSON with:
- main_concept: the central concept (5 words max)
- details: array of 2-3 supporting details (10 words each max)

JSON:"""

    params = call_ollama_json(prompt)

    main_concept = params.get("main_concept", scene['title'][:30])
    details = params.get("details", ["Detail 1", "Detail 2"])

    detail_code = "\n".join([
        f'            Text("- {d[:80]}", font_size=22, color=WHITE),'
        for d in details[:3]
    ])

    return {
        "main_concept": main_concept[:40],
        "detail_points_code": detail_code
    }
