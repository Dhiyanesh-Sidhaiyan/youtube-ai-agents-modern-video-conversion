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
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama is not running. Start it with: ollama serve\n"
            "Then pull the model: ollama pull phi4"
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


if __name__ == "__main__":
    import sys

    abstract = sys.argv[1] if len(sys.argv) > 1 else "abstracts.txt"
    output = sys.argv[2] if len(sys.argv) > 2 else "output/script.json"
    generate_script(abstract, output)
