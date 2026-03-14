"""Parameter extractor for info card template"""
import re
from agents.templates.utils import all_points_generic, call_ollama_json, extract_bullet_points_from_narration, log_extraction_warning

def extract_info_card_params(scene: dict) -> dict:
    """Extract parameters for Claude-style info card template with content-aware fallback."""
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', '')
    narration = scene.get('narration_text', '')

    prompt = f"""Extract overview and key points from this content.

Title: {title}
Visual Description: {scene.get('visual_description', '')}
Narration: {narration}

Return JSON with SPECIFIC content from the narration:
- overview_text: main explanation (max 80 chars) - summarize the key idea
- key_points: array of 3-4 important points (max 40 chars each) - actual points mentioned

DO NOT use "Point 1", "Point 2" - extract actual key points from content.

JSON:"""

    params = call_ollama_json(prompt, retry_on_fail=True)

    overview = params.get("overview_text", "")
    key_points = params.get("key_points", [])

    # Validate overview
    if not overview or overview == "This topic covers important concepts.":
        # Extract first meaningful sentence from narration
        sentences = re.split(r'[.!?]+', narration)
        overview = next((s.strip()[:80] for s in sentences if len(s.strip()) > 20), title)

    # Validate key points
    if all_points_generic(key_points):
        log_extraction_warning(scene_id, "Info card: Using content-aware point extraction")
        key_points = extract_bullet_points_from_narration(narration, count=4)

    # Ensure points are strings
    key_points = [str(p)[:40] for p in key_points[:4]]

    # Ensure at least one point
    if not key_points:
        key_points = [narration[:40] if narration else title[:40]]

    # Generate Manim code for points
    points_code = "\n".join([
        f'            Text("• {p}", font_size=18, color="#c0caf5"),'
        for p in key_points
    ])

    return {
        "overview_text": overview[:80],
        "key_points_code": points_code
    }
