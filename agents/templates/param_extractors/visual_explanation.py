"""Parameter extractor for visual explanation template"""
import re
from agents.templates.utils import all_points_generic, call_ollama_json, extract_bullet_points_from_narration, log_extraction_warning

def extract_visual_explanation_params(scene: dict) -> dict:
    """Extract parameters for Claude-style visual explanation template with content-aware fallback."""
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', '')
    narration = scene.get('narration_text', '')

    prompt = f"""Extract a comparison with two options from this content.

Title: {title}
Visual Description: {scene.get('visual_description', '')}
Narration: {narration}

Return JSON with SPECIFIC content from the narration:
- option_a_label: name of first option (max 20 chars)
- option_a_points: array of 3 points supporting option A (max 35 chars each)
- option_b_label: name of second option (max 20 chars)
- option_b_points: array of 3 points supporting option B (max 35 chars each)
- recommendation: recommendation text (max 50 chars)

DO NOT use "Option A/B" or "Point 1/2/3" - extract actual options and points.

JSON:"""

    params = call_ollama_json(prompt, retry_on_fail=True)

    option_a_label = params.get("option_a_label", "")
    option_b_label = params.get("option_b_label", "")
    option_a_points = params.get("option_a_points", [])
    option_b_points = params.get("option_b_points", [])
    recommendation = params.get("recommendation", "")

    # Validate labels
    if not option_a_label or option_a_label == "Option A":
        # Try to extract from title
        vs_match = re.search(r'(.+?)\s+(?:vs\.?|versus|and|or)\s+(.+)', title, re.IGNORECASE)
        if vs_match:
            option_a_label = vs_match.group(1).strip()[:20]
            option_b_label = vs_match.group(2).strip()[:20]
        else:
            option_a_label = "Approach"
            option_b_label = "Alternative"

    if not option_b_label or option_b_label == "Option B":
        option_b_label = "Alternative"

    # Validate points
    if all_points_generic(option_a_points) or all_points_generic(option_b_points):
        log_extraction_warning(scene_id, "Visual explanation: Using content-aware point extraction")
        points = extract_bullet_points_from_narration(narration, count=6)
        mid = len(points) // 2
        option_a_points = points[:mid] if mid > 0 else points[:3]
        option_b_points = points[mid:] if mid > 0 else points[:3]

    # Validate recommendation
    if not recommendation or "Consider both" in recommendation:
        recommendation = f"Choose based on your {title[:20]} needs"

    # Ensure points are strings
    option_a_points = [str(p)[:35] for p in option_a_points[:3]]
    option_b_points = [str(p)[:35] for p in option_b_points[:3]]

    # Ensure at least one point each
    if not option_a_points:
        option_a_points = [f"Key aspect of {option_a_label}"]
    if not option_b_points:
        option_b_points = [f"Key aspect of {option_b_label}"]

    # Generate Manim code for points
    option_a_code = "\n".join([
        f'            Text("• {p}", font_size=18, color="#c0caf5"),'
        for p in option_a_points
    ])
    option_b_code = "\n".join([
        f'            Text("• {p}", font_size=18, color="#c0caf5"),'
        for p in option_b_points
    ])

    return {
        "option_a_label": option_a_label[:20],
        "option_b_label": option_b_label[:20],
        "option_a_points_code": option_a_code,
        "option_b_points_code": option_b_code,
        "recommendation": recommendation[:50]
    }
