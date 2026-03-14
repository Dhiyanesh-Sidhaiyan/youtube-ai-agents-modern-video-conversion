"""Parameter extractor for conclusion template"""
from agents.templates.utils import all_points_generic, call_ollama_json, extract_bullet_points_from_narration, log_extraction_warning

def extract_conclusion_params(scene: dict) -> dict:
    """Extract parameters for conclusion template with content-aware fallback."""
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', '')
    narration = scene.get('narration_text', '')

    prompt = f"""Extract parameters for a conclusion animation.

Title: {title}
Visual Description: {scene.get('visual_description', '')}
Narration: {narration}

Return JSON with SPECIFIC content:
- takeaways: array of 3-4 key takeaways (10 words each max) - actual lessons from content
- final_message: inspiring final message (8 words max)

DO NOT use "Key point 1", "Key point 2" - use actual takeaways from the narration.

JSON:"""

    params = call_ollama_json(prompt, retry_on_fail=True)

    takeaways = params.get("takeaways", [])
    final_message = params.get("final_message", "")

    # Validate takeaways
    if all_points_generic(takeaways):
        log_extraction_warning(scene_id, "Conclusion: Using content-aware takeaway extraction")
        takeaways = extract_bullet_points_from_narration(narration, count=3)

    # Validate final message
    if not final_message or final_message == "Thank you for watching!":
        # Create a relevant closing based on title
        if title:
            final_message = f"Now you understand {title[:25]}!"
        else:
            final_message = "Apply these concepts today!"

    takeaway_code = "\n".join([
        f'            Text("{i+1}. {str(t)[:45]}", font_size=26, color=WHITE),'
        for i, t in enumerate(takeaways[:4])
    ])

    return {
        "takeaway_points_code": takeaway_code,
        "final_message": final_message[:50]
    }


# ─── Advanced Template Parameter Extractors ─────────────────────────────────
