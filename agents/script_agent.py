"""
Agent 1: Research & Script Agent
Converts a research paper abstract into a structured scene-by-scene script
using Mayer's Multimedia Learning Principles via a local Ollama LLM.
"""

import json
import re
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi4"
OLLAMA_TIMEOUT = 300  # 5 minutes for large transcripts

SYSTEM_PROMPT = """You are an expert educational video scriptwriter specializing in
Indian higher education. You apply Mayer's Multimedia Learning Principles:
1. Coherence - include only relevant material
2. Signaling - highlight key concepts
3. Redundancy - narration alone conveys content (no duplicate on-screen text)
4. Spatial/Temporal Contiguity - align narration with visuals
5. Segmenting - break into learner-paced scenes"""

SCENE_PROMPT = """Given the research paper abstract below, create a structured video script
with exactly 6 scenes. Each scene should take approximately 30-45 seconds of narration.

Abstract:
{abstract}

Return ONLY valid JSON (no markdown, no code fences) with this exact structure:
{{
  "title": "video title",
  "total_scenes": 6,
  "scenes": [
    {{
      "scene_id": 1,
      "title": "Scene title",
      "narration_text": "What the narrator speaks. 3-5 sentences. Simple, clear language.",
      "visual_description": "What appears on screen. Describe shapes, text, arrows, diagrams. Be specific for Manim animation."
    }}
  ]
}}

Scene progression: 1=Problem/Hook, 2=Context, 3=Framework Overview, 4=Agent Details,
5=Implementation/Demo, 6=Impact/Conclusion"""


def call_ollama(prompt: str, model: str = MODEL) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 2048},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama is not running. Start it with: ollama serve\n"
            "Then pull the model: ollama pull phi4"
        )
    except requests.exceptions.ReadTimeout:
        raise RuntimeError(
            f"Ollama timed out after {OLLAMA_TIMEOUT}s. The model may be loading or busy.\n"
            "Try again - phi4 on CPU can take 3-5 minutes for large prompts."
        )


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, stripping any surrounding markdown."""
    # Remove code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Find the outermost JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No valid JSON found in LLM response:\n{text[:500]}")


def generate_script(abstract_path: str, output_path: str) -> dict:
    """Read abstract, generate structured script, save to JSON."""
    with open(abstract_path, "r") as f:
        abstract = f.read().strip()

    prompt = f"{SYSTEM_PROMPT}\n\n{SCENE_PROMPT.format(abstract=abstract)}"

    print("[Script Agent] Calling LLM to generate script...")
    raw = call_ollama(prompt)

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


# ─── Transcript-based Script Generation ────────────────────────────────────

TRANSCRIPT_PROMPT = """You are creating an educational video script from a YouTube video transcript.

TRANSCRIPT SUMMARY:
{summary}

KEY CONCEPTS:
{key_concepts}

FULL TRANSCRIPT EXCERPT:
{transcript_excerpt}

Generate exactly {scene_count} scenes. Each scene should:
1. Have a clear, descriptive title
2. Have 3-5 sentences of narration (conversational, educational tone)
3. Have a visual_description for Manim animation (shapes, diagrams, text)
4. Include a scene_type from: "intro", "concept", "comparison", "process", "example", "conclusion"

Scene progression guidelines:
- Scene 1: Always "intro" - introduce topic and hook audience
- Middle scenes: Mix of "concept", "comparison", "process", "example" based on content
- Final scene: Always "conclusion" - summarize and provide takeaways

Return ONLY valid JSON (no markdown, no code fences):
{{
  "title": "video title based on content",
  "total_scenes": {scene_count},
  "source": "youtube_transcript",
  "scenes": [
    {{
      "scene_id": 1,
      "scene_type": "intro",
      "title": "Scene title",
      "narration_text": "What the narrator speaks. 3-5 sentences.",
      "visual_description": "What appears on screen. Be specific for Manim."
    }}
  ]
}}"""


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

    Args:
        transcript_data: Dict with keys: summary, key_concepts, full_text, duration_minutes
        output_path: Where to save the script JSON

    Returns:
        Script dict with scene_type for each scene
    """
    duration = transcript_data.get("duration_minutes", 5)
    word_count = transcript_data.get("word_count", 500)
    summary = transcript_data.get("summary", "")
    key_concepts = transcript_data.get("key_concepts", [])
    full_text = transcript_data.get("full_text", "")

    # Compute scene count
    scene_count = compute_scene_count(duration, word_count)

    # Prepare prompt
    prompt = f"{SYSTEM_PROMPT}\n\n{TRANSCRIPT_PROMPT.format(
        summary=summary,
        key_concepts=', '.join(key_concepts),
        transcript_excerpt=full_text[:4000],  # Limit to avoid token overflow
        scene_count=scene_count
    )}"

    print(f"\n[Script Agent] Generating script from transcript...")
    print(f"  Duration: {duration} min | Words: {word_count} | Target scenes: {scene_count}")

    raw = call_ollama(prompt)
    script = extract_json(raw)

    # Validate and ensure scene_type exists
    assert "scenes" in script, "Missing 'scenes' key in script"

    scene_types = ["intro", "concept", "comparison", "process", "example", "conclusion"]
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
