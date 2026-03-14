"""Parameter extractor for intro template"""
from agents.templates.utils import all_points_generic, call_ollama_json, extract_bullet_points_from_narration, log_extraction_warning

def extract_intro_params(scene: dict) -> dict:
    """Extract parameters for intro template with content-aware fallback."""
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', '')
    narration = scene.get('narration_text', '')

    prompt = f"""Extract parameters for an intro animation from this scene.

Title: {title}
Visual Description: {scene.get('visual_description', '')}
Narration: {narration}

Return JSON with SPECIFIC content from the narration:
- subtitle: 1-line subtitle (10 words max) - summarize the main topic
- bullet_points: array of 3-4 key points (8 words each max) - extract actual points mentioned

DO NOT use generic "Point 1", "Point 2" - use actual content.

JSON:"""

    params = call_ollama_json(prompt, retry_on_fail=True)

    # Extract with validation
    subtitle = params.get("subtitle", "")
    points = params.get("bullet_points", [])

    # Validate subtitle
    if not subtitle or subtitle == "Key Concepts":
        # Extract from narration - first meaningful phrase
        words = narration.split()[:10] if narration else title.split()[:5]
        subtitle = ' '.join(words) + "..."

    # Validate points - check for generic content
    if all_points_generic(points):
        log_extraction_warning(scene_id, "Intro: Using content-aware bullet extraction")
        points = extract_bullet_points_from_narration(narration, count=3)

    # Generate Manim code for bullets
    bullet_code = "\n".join([
        f'            Text("* {str(p)[:80]}", font_size=24, color=WHITE),'
        for p in points[:4]
    ])

    return {
        "subtitle": subtitle[:100],
        "bullet_points_code": bullet_code
    }
