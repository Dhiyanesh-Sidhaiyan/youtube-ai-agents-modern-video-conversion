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
FALLBACK_MODEL = "llama3"  # Faster model for long transcripts
OLLAMA_TIMEOUT = 600  # 10 minutes for very long transcripts

SYSTEM_PROMPT = """You are a world-class educational video producer creating NOTEBOOKLM-QUALITY content.

═══════════════════════════════════════════════════════════════════════════════
NOTEBOOKLM PRINCIPLES (conversational, engaging, memorable):
═══════════════════════════════════════════════════════════════════════════════

1. CONVERSATIONAL TONE - Not a lecture, but explaining to a curious friend
   - "You might wonder..." instead of "We will discuss..."
   - "Here's the cool part..." instead of "The following point is..."
   - Ask rhetorical questions to build curiosity

2. ANALOGIES FIRST - Every abstract concept needs a concrete comparison
   - "Think of neural networks like a library where books organize themselves..."
   - "API is like a restaurant menu - you order, the kitchen handles the complexity"
   - Split screen: abstract concept on left, everyday analogy on right

3. NARRATIVE ARC - Build tension and release
   - Setup: What problem are we solving?
   - Tension: What makes this hard? "But wait..."
   - Climax: The key insight or "aha moment"
   - Resolution: What can viewers do with this?

4. SPECIFICITY OVER GENERIC - Never use placeholder content
   - BAD: "Step 1, Step 2, Step 3"
   - GOOD: "First, collect the data. Then, clean out the noise. Finally, train the model."

5. NATURAL PAUSES - Moments for concepts to sink in
   - After surprising facts: "Let that sink in..."
   - Before reveals: "So what's the solution?"

═══════════════════════════════════════════════════════════════════════════════
ENGAGEMENT PRINCIPLES (make videos people WANT to watch):
═══════════════════════════════════════════════════════════════════════════════

1. HOOK FIRST - Start with a compelling question, surprising fact, or relatable problem
2. VISUAL STORYTELLING - Every concept needs a visual metaphor (don't just show text!)
3. PROGRESSIVE REVELATION - Build up complexity, reveal insights step-by-step
4. EMOTIONAL CONNECTION - Use scenarios viewers relate to
5. CLEAR TAKEAWAYS - End each section with "aha moment"

═══════════════════════════════════════════════════════════════════════════════
ANTI-GENERIC RULES (CRITICAL - never break these):
═══════════════════════════════════════════════════════════════════════════════

NEVER generate:
- "Step 1", "Step 2", "Step 3" without specific content from the transcript
- Generic bullet points like "Point 1", "Feature A", "Item 1"
- Placeholder text - always extract actual content from the source
- Repetitive scene structures - vary your visual approaches

IF you cannot extract specific content:
- Quote directly from the transcript
- Ask a rhetorical question instead
- Use an analogy to explain the concept
- Describe what the viewer should be thinking/feeling

═══════════════════════════════════════════════════════════════════════════════
LEARNING SCIENCE (Mayer's Multimedia Principles):
═══════════════════════════════════════════════════════════════════════════════

- Coherence: Only relevant material, no filler
- Signaling: Highlight key concepts visually
- Segmenting: Break into digestible scenes (30-45 sec each)

═══════════════════════════════════════════════════════════════════════════════
VISUAL DESIGN INTELLIGENCE:
═══════════════════════════════════════════════════════════════════════════════

- Use COMPARISONS (before/after, option A vs B) to clarify choices
- Use DIAGRAMS with connections to show relationships
- Use TIMELINES for sequences and progressions
- Use DATA VISUALIZATIONS for statistics and metrics
- Use HIERARCHIES for categorization and structure
- Use ANALOGIES with split-screen (abstract concept + everyday comparison)
- Avoid walls of text - prefer icons, shapes, and visual metaphors"""

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


def call_ollama(prompt: str, model: str = MODEL, timeout: int = OLLAMA_TIMEOUT) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 2048},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama is not running. Start it with: ollama serve\n"
            "Then pull the model: ollama pull phi4"
        )
    except requests.exceptions.ReadTimeout:
        # Try fallback model if primary times out
        if model != FALLBACK_MODEL:
            print(f"  {model} timed out, trying faster {FALLBACK_MODEL}...")
            return call_ollama(prompt, model=FALLBACK_MODEL, timeout=timeout)
        raise RuntimeError(
            f"Ollama timed out after {timeout}s with both models.\n"
            "The transcript may be too long. Try a shorter video."
        )


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling common LLM output issues."""
    # Remove code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = re.sub(r"```", "", text).strip()

    # Find the outermost JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No valid JSON found in LLM response:\n{text[:500]}")

    json_str = match.group()

    # Fix common LLM JSON issues
    # 1. Remove trailing commas before } or ]
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

    # 2. Remove control characters that break JSON
    json_str = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", json_str)

    # 3. Fix unescaped newlines inside strings (replace with space)
    # This is tricky - we do a simple fix for common cases
    json_str = json_str.replace("\n", " ").replace("\r", " ")

    # 4. Remove // comments (common LLM mistake)
    json_str = re.sub(r"//.*?(?=[\n\r,}\]])", "", json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Try one more fix: sometimes LLMs use single quotes
        try:
            # Replace single quotes with double quotes (careful with apostrophes)
            fixed = re.sub(r"'([^']*)':", r'"\1":', json_str)
            fixed = re.sub(r":\s*'([^']*)'", r': "\1"', fixed)
            return json.loads(fixed)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from LLM: {e}\n{json_str[:500]}")


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

TRANSCRIPT_PROMPT = """You are a GENIUS educational content creator making NOTEBOOKLM-QUALITY animated videos.

═══════════════════════════════════════════════════════════════════════════════
CONTENT TO TRANSFORM:
═══════════════════════════════════════════════════════════════════════════════

SUMMARY: {summary}

KEY CONCEPTS: {key_concepts}

NARRATIVE STRUCTURE: {narrative_structure}

EXTRACTED ANALOGIES/EXAMPLES: {extracted_content}

TRANSCRIPT EXCERPT: {transcript_excerpt}

═══════════════════════════════════════════════════════════════════════════════
ANALOGY GENERATION (NotebookLM-style - REQUIRED for every 2 scenes):
═══════════════════════════════════════════════════════════════════════════════

For each KEY CONCEPT, create a memorable analogy:
- Use everyday objects/experiences that everyone understands
- Format: "Think of [concept] like [everyday thing]..."
- Make it visual: "Imagine if [abstract] were a [concrete]..."

EXAMPLE ANALOGIES:
- "Gradient descent is like a ball rolling downhill - always seeking the lowest point"
- "A database index is like a book's index - find what you need without reading everything"
- "Recursion is like Russian nesting dolls - each contains a smaller version of itself"
- "Machine learning is like teaching a child - show examples, not rules"

IN VISUAL_DESCRIPTION for analogies, include:
- "Split screen: Left shows [abstract concept], Right shows [analogy animation]"
- "Transition from real-world example to technical representation"
- "Side-by-side: everyday scenario morphs into code/diagram"

═══════════════════════════════════════════════════════════════════════════════
YOUR MISSION: Create {scene_count} ENGAGING scenes that make learning EXCITING
═══════════════════════════════════════════════════════════════════════════════

SCENE TYPE SELECTION GUIDE (pick the BEST visual for each concept):

📊 DATA/NUMBERS mentioned? → Use "data_chart" or "metrics"
   Example: "80% of projects fail" → animated bar chart showing 80%

⚖️ TWO OPTIONS or TRADE-OFFS? → Use "visual_explanation" or "comparison"
   Example: "React vs Vue" → side-by-side comparison boxes

🔄 SEQUENCE or STEPS? → Use "process", "timeline", or "decision_tree"
   Example: "First, then, finally" → connected flow diagram

🔗 RELATIONSHIPS or CATEGORIES? → Use "diagram" or "hierarchy"
   Example: "Components depend on..." → radial diagram with arrows

📝 EXPLAINING A CONCEPT? → Use "info_card" or "concept"
   Example: "What is REST API?" → overview box with key points

═══════════════════════════════════════════════════════════════════════════════
MATHEMATICAL CONTENT DETECTION (use LaTeX-enhanced templates):
═══════════════════════════════════════════════════════════════════════════════

🧮 EQUATIONS/FORMULAS? → Use "math_formula" or "equation_derivation"
   - Simple equation (E=mc²): "math_formula" - single equation with explanation
   - Step-by-step solving: "equation_derivation" - shows transformation steps
   Example: "Let's derive the quadratic formula" → equation_derivation with steps

📈 FUNCTIONS/GRAPHS? → Use "graph_visualization"
   - Plotting functions (f(x), curves, slopes)
   - Coordinate systems with labeled axes
   Example: "y = x² creates a parabola" → graph with curve and key points

📐 SHAPES/THEOREMS? → Use "geometric_theorem"
   - Pythagorean theorem, circle properties, angles
   - Visual proof with shapes and labels
   Example: "a² + b² = c²" → right triangle with labeled sides and proof steps

🔢 MATRICES/VECTORS? → Use "matrix_operation"
   - Matrix multiplication, determinants, transformations
   - Animated row-column highlighting
   Example: "Multiply these matrices" → matrix A × B = C with step animation

═══════════════════════════════════════════════════════════════════════════════
VISUAL DESCRIPTION EXAMPLES (be THIS specific):
═══════════════════════════════════════════════════════════════════════════════

BAD: "Show text about machine learning"
GOOD: "Central circle labeled 'ML' with 4 connected nodes: 'Data', 'Model', 'Training', 'Prediction' - arrows flow clockwise"

BAD: "Display comparison"
GOOD: "Two boxes side by side: Left box 'Traditional' (red border) with 3 bullet cons, Right box 'Modern' (green border) with 3 bullet pros, recommendation banner at bottom"

BAD: "Show the process"
GOOD: "5 connected steps flowing down: 'Input' → 'Process' → 'Validate' → 'Transform' → 'Output', each step in a rounded box with number badge"

═══════════════════════════════════════════════════════════════════════════════
SCENE STRUCTURE:
═══════════════════════════════════════════════════════════════════════════════

Scene 1: "intro" - Hook with question/statistic, preview key concepts
Scene 2-{middle_count}: Mix of advanced types based on content
Final Scene: "conclusion" - Key takeaways, call to action

Return ONLY valid JSON:
{{
  "title": "Compelling video title",
  "total_scenes": {scene_count},
  "source": "youtube_transcript",
  "scenes": [
    {{
      "scene_id": 1,
      "scene_type": "intro",
      "title": "Hook title",
      "narration_text": "Engaging narration (3-5 sentences, conversational)",
      "visual_description": "SPECIFIC visual layout with shapes, connections, colors"
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
        use_model = MODEL
    else:
        excerpt_limit = 4000
        use_model = MODEL

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
    if use_model != MODEL:
        print(f"  Using faster model ({use_model}) for long transcript")

    raw = call_ollama(prompt, model=use_model)
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
