"""Parameter extractor for process template"""
from agents.templates.utils import all_steps_generic, call_ollama_json, extract_steps_from_narration, log_extraction_warning

def extract_process_params(scene: dict) -> dict:
    """
    Extract parameters for process flow template.
    Uses retry logic and content-aware fallback to avoid generic content.
    """
    scene_id = scene.get('scene_id', 0)
    title = scene.get('title', 'Process')
    visual_desc = scene.get('visual_description', '')
    narration = scene.get('narration_text', '')

    # Primary extraction prompt - more specific instructions
    prompt = f"""Extract SPECIFIC process steps from this content. DO NOT use generic placeholders.

Title: {title}
Visual Description: {visual_desc}
Narration: {narration}

IMPORTANT: Extract the ACTUAL steps mentioned in the narration/description.
DO NOT return generic "Step 1", "Step 2" without real content.

Return JSON with:
- steps: array of [["step_name", "description"], ...] where:
  - step_name: SHORT label (2-4 words) describing the action
  - description: SPECIFIC detail from the content (not generic)
  - 3-5 steps total

Example good output: [["Data Input", "User enters credentials"], ["Validation", "System checks format"], ["Processing", "Backend authenticates"]]
Example bad output: [["Step 1", ""], ["Step 2", ""], ["Step 3", ""]]

JSON:"""

    # First attempt with retry enabled
    params = call_ollama_json(prompt, retry_on_fail=True)
    steps = params.get("steps", [])

    # Check if extraction returned generic content
    if all_steps_generic(steps):
        log_extraction_warning(scene_id, "LLM returned generic steps, trying simplified prompt...")

        # Retry with simpler, more focused prompt
        simplified_prompt = f"""Read this text and list 3-4 key actions or stages mentioned:

"{narration[:500]}"

Return JSON: {{"steps": [["Action1", "detail"], ["Action2", "detail"], ...]}}
JSON:"""

        params = call_ollama_json(simplified_prompt, timeout=PARAM_EXTRACTOR_RETRY_TIMEOUT)
        steps = params.get("steps", [])

    # If still generic, use content-aware extraction from narration
    if all_steps_generic(steps):
        log_extraction_warning(scene_id, "Using content-aware extraction from narration...")
        steps = extract_steps_from_narration(narration, title)

    # Final validation - NEVER return fully generic steps
    if all_steps_generic(steps):
        log_extraction_warning(scene_id, "CRITICAL: Could not extract specific steps, using narration excerpt")
        # Use narration chunks as steps rather than generic placeholders
        narration_words = narration.split() if narration else title.split()
        if len(narration_words) > 15:
            # Split narration into 3 meaningful chunks
            chunk_size = len(narration_words) // 3
            steps = [
                ["Begin", ' '.join(narration_words[:chunk_size])[:40]],
                ["Process", ' '.join(narration_words[chunk_size:2*chunk_size])[:40]],
                ["Complete", ' '.join(narration_words[2*chunk_size:])[:40]]
            ]
        else:
            steps = [[title[:15], narration[:50] if narration else "See demonstration"]]

    # Format and clean steps
    step_data = []
    for step in steps[:5]:
        if isinstance(step, (list, tuple)) and len(step) >= 2:
            name = str(step[0])[:15].strip() or "Step"
            desc = str(step[1])[:40].strip() or ""
            step_data.append([name, desc])
        elif isinstance(step, (list, tuple)) and len(step) == 1:
            step_data.append([str(step[0])[:15].strip(), ""])
        else:
            step_data.append([str(step)[:15].strip(), ""])

    # Ensure at least 2 steps
    while len(step_data) < 2:
        step_data.append(["Continue", "Next phase"])

    return {
        "step_data": repr(step_data)
    }
