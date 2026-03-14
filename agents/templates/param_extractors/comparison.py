"""Parameter extractor for comparison template"""
import re
from agents.templates.utils import all_points_generic, call_ollama_json, log_extraction_warning

def extract_comparison_params(scene: dict) -> dict:
    """Extract parameters for comparison template with content-aware fallback."""
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', '')
    narration = scene.get('narration_text', '')

    prompt = f"""Extract parameters for a comparison animation.

Title: {title}
Visual Description: {scene.get('visual_description', '')}
Narration: {narration}

Return JSON with SPECIFIC content being compared:
- left_label: label for left side (what is being compared)
- left_items: array of 2-3 specific characteristics
- right_label: label for right side (the other thing)
- right_items: array of 2-3 specific characteristics

DO NOT use "Option A/B" or "Item 1/2" - extract actual compared items from content.

JSON:"""

    params = call_ollama_json(prompt, retry_on_fail=True)

    left_label = params.get("left_label", "")
    right_label = params.get("right_label", "")
    left_items = params.get("left_items", [])
    right_items = params.get("right_items", [])

    # Validate labels - extract from title if generic
    if not left_label or left_label in ["Option A", "Left"]:
        # Try to extract from title like "X vs Y" or "X and Y"
        vs_match = re.search(r'(.+?)\s+(?:vs\.?|versus|and|or)\s+(.+)', title, re.IGNORECASE)
        if vs_match:
            left_label = vs_match.group(1).strip()[:25]
            right_label = vs_match.group(2).strip()[:25]
        else:
            left_label = "Approach 1"
            right_label = "Approach 2"

    if not right_label or right_label in ["Option B", "Right"]:
        right_label = "Alternative"

    # Validate items
    if all_points_generic(left_items) or all_points_generic(right_items):
        log_extraction_warning(scene_id, "Comparison: Using content-aware item extraction")
        # Split narration for left/right items
        sentences = re.split(r'[.!?]+', narration)
        mid = len(sentences) // 2
        left_items = [s.strip()[:30] for s in sentences[:mid] if len(s.strip()) > 10][:3]
        right_items = [s.strip()[:30] for s in sentences[mid:] if len(s.strip()) > 10][:3]

        if not left_items:
            left_items = [f"Aspect of {left_label}"]
        if not right_items:
            right_items = [f"Aspect of {right_label}"]

    # Ensure items are strings
    left_items = [str(i)[:30] if not isinstance(i, str) else i[:30] for i in left_items]
    right_items = [str(i)[:30] if not isinstance(i, str) else i[:30] for i in right_items]

    left_code = "\n".join([
        f'            Text("* {i[:30]}", font_size=20, color=WHITE),'
        for i in left_items[:3]
    ])
    right_code = "\n".join([
        f'            Text("* {i[:30]}", font_size=20, color=WHITE),'
        for i in right_items[:3]
    ])

    return {
        "left_label": left_label[:25],
        "right_label": right_label[:25],
        "left_items_code": left_code,
        "right_items_code": right_code
    }
