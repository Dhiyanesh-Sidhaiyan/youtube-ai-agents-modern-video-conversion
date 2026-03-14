"""
Agent 1: Research & Script Agent
Converts a research paper abstract into a structured scene-by-scene script
using Mayer's Multimedia Learning Principles via a local Ollama LLM.
"""

import json

from core.ollama_client import call_ollama
from core.llm_utils import extract_json
from core.config import SCRIPT_MODEL, FALLBACK_MODEL, TIMEOUT_SCRIPT
from prompts.script_prompts import SYSTEM_PROMPT, SCENE_PROMPT, TRANSCRIPT_PROMPT

MODEL = SCRIPT_MODEL


def generate_script(abstract_path: str, output_path: str) -> dict:
    """Read abstract, generate structured script, save to JSON."""
    with open(abstract_path, "r") as f:
        abstract = f.read().strip()

    prompt = f"{SYSTEM_PROMPT}\n\n{SCENE_PROMPT.format(abstract=abstract)}"

    print("[Script Agent] Calling LLM to generate script...")
    raw = call_ollama(prompt, model=MODEL, timeout=TIMEOUT_SCRIPT)

    script = extract_json(raw)

    # Validate structure
    assert "scenes" in script, "Missing 'scenes' key in script"
    assert len(script["scenes"]) >= 5, f"Too few scenes: {len(script['scenes'])}"
    for scene in script["scenes"]:
        for key in ("scene_id", "title", "narration_text", "visual_description"):
            assert key in scene, f"Scene missing key: {key}"

    with open(output_path, "w") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)

    print(f"[Script Agent] Script saved → {output_path}")
    print(f"  Title: {script['title']}")
    print(f"  Scenes: {len(script['scenes'])}")
    return script


# ─── Transcript-based Script Generation ─────────────────────────────────────


def compute_scene_count(duration_minutes: int, word_count: int) -> int:
    """
    Compute optimal scene count based on video duration.
    - Short videos (< 5 min): 3-4 scenes
    - Medium videos (5-15 min): 5-7 scenes
    - Long videos (> 15 min): 8-10 scenes
    """
    if duration_minutes < 3:
        return 3
    elif duration_minutes < 5:
        return 4
    elif duration_minutes < 10:
        return 5
    elif duration_minutes < 15:
        return 6
    elif duration_minutes < 25:
        return 8
    else:
        return min(10, duration_minutes // 3)


def generate_script_from_transcript(
    transcript_data: dict,
    output_path: str = "output/script.json"
) -> dict:
    """
    Generate script from preprocessed YouTube transcript with DYNAMIC scene count.
    Uses NotebookLM-style deep content extraction when available.

    Args:
        transcript_data: Dict with keys: summary, key_concepts, full_text, duration_minutes,
                        and optionally deep_content (from chunk-based extraction)
        output_path: Where to save the script JSON

    Returns:
        Script dict with scene_type for each scene
    """
    duration = transcript_data.get("duration_minutes", 5)
    word_count = transcript_data.get("word_count", 500)
    summary = transcript_data.get("summary", "")
    key_concepts = transcript_data.get("key_concepts", [])
    full_text = transcript_data.get("full_text", "")

    # Get deep content if available (NotebookLM-style extraction)
    deep_content = transcript_data.get("deep_content", {})

    # Compute scene count
    scene_count = compute_scene_count(duration, word_count)

    # Determine transcript excerpt size based on length
    # Longer transcripts get more aggressive truncation to avoid timeouts
    if word_count > 5000:
        excerpt_limit = 2500  # Very long - rely more on summary
        use_model = FALLBACK_MODEL  # Use faster model
    elif word_count > 3000:
        excerpt_limit = 3500
        use_model = SCRIPT_MODEL
    else:
        excerpt_limit = 4000
        use_model = SCRIPT_MODEL

    # Prepare narrative structure (from deep content or empty)
    narrative = deep_content.get("narrative", {}) if deep_content else {}
    narrative_str = ""
    if narrative:
        narrative_str = f"""
Hook: {narrative.get('hook', 'N/A')}
Setup: {narrative.get('setup', 'N/A')}
Tension: {narrative.get('tension', 'N/A')}
Climax: {narrative.get('climax', 'N/A')}
Resolution: {narrative.get('resolution', 'N/A')}"""
    else:
        narrative_str = "Not available - extract from transcript"

    # Prepare extracted content (analogies, examples from deep content)
    chunk_content = deep_content.get("chunk_content", {}) if deep_content else {}
    extracted_str = ""
    if chunk_content:
        analogies = chunk_content.get("analogies", [])
        examples = chunk_content.get("examples", [])
        quotes = chunk_content.get("quotes", [])

        parts = []
        if analogies:
            parts.append(f"Analogies: {', '.join(str(a) for a in analogies[:5])}")
        if examples:
            parts.append(f"Examples: {', '.join(str(e) for e in examples[:5])}")
        if quotes:
            parts.append(f"Memorable phrases: {', '.join(str(q) for q in quotes[:3])}")

        extracted_str = "\n".join(parts) if parts else "Use transcript to create analogies"
    else:
        extracted_str = "Generate analogies from the concepts above"

    # Prepare prompt
    middle_count = scene_count - 1  # Exclude intro scene from middle count display
    prompt = f"{SYSTEM_PROMPT}\n\n{TRANSCRIPT_PROMPT.format(
        summary=summary,
        key_concepts=', '.join(key_concepts),
        narrative_structure=narrative_str,
        extracted_content=extracted_str,
        transcript_excerpt=full_text[:excerpt_limit],
        scene_count=scene_count,
        middle_count=middle_count
    )}"

    # Log deep content usage
    if deep_content:
        print(f"  [NotebookLM] Using deep content: narrative + {len(chunk_content.get('analogies', []))} analogies")

    print(f"\n[Script Agent] Generating script from transcript...")
    print(f"  Duration: {duration} min | Words: {word_count} | Target scenes: {scene_count}")
    if use_model != SCRIPT_MODEL:
        print(f"  Using faster model ({use_model}) for long transcript")

    raw = call_ollama(prompt, model=use_model, timeout=TIMEOUT_SCRIPT)
    script = extract_json(raw)

    # Validate and ensure scene_type exists
    assert "scenes" in script, "Missing 'scenes' key in script"

    scene_types = [
        "intro", "concept", "comparison", "process", "example", "conclusion",
        "data_chart", "math_formula", "timeline", "diagram", "metrics", "hierarchy",
        "visual_explanation", "info_card", "decision_tree",
        # LaTeX-enhanced templates
        "equation_derivation", "graph_visualization", "geometric_theorem", "matrix_operation"
    ]
    for i, scene in enumerate(script["scenes"]):
        for key in ("scene_id", "title", "narration_text", "visual_description"):
            if key not in scene:
                scene[key] = f"Default {key}" if key != "scene_id" else i + 1

        # Ensure scene_type
        if "scene_type" not in scene or scene["scene_type"] not in scene_types:
            if i == 0:
                scene["scene_type"] = "intro"
            elif i == len(script["scenes"]) - 1:
                scene["scene_type"] = "conclusion"
            else:
                scene["scene_type"] = "concept"

    # Attach key_concepts to intro/conclusion scenes for dynamic hook generation
    if key_concepts:
        for scene in script["scenes"]:
            if scene.get("scene_type") in ("intro", "conclusion"):
                scene["key_concepts"] = key_concepts[:6]

    # Save
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)

    print(f"[Script Agent] Script saved → {output_path}")
    print(f"  Title: {script.get('title', 'Untitled')}")
    print(f"  Scenes: {len(script['scenes'])}")
    for s in script["scenes"]:
        print(f"    {s['scene_id']}. [{s['scene_type']}] {s['title']}")

    return script


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "output/script.json"

        # Check if input is a transcript JSON or abstract text
        if input_file.endswith(".json"):
            with open(input_file) as f:
                transcript_data = json.load(f)
            generate_script_from_transcript(transcript_data, output)
        else:
            generate_script(input_file, output)
    else:
        print("Usage: python script_agent.py <abstract.txt|transcript.json> [output.json]")
