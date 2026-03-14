"""
NotebookLM-style deep content extraction from transcripts.

Responsibility: Chunk-based processing and narrative structure analysis.
This is the "deep" layer — chunk the transcript, extract structured content
from each chunk, and identify the narrative arc for storytelling.
"""

import json
import re

from core.ollama_client import call_ollama
from core.config import SCRIPT_MODEL, TIMEOUT_MEDIUM

SUMMARIZER_MODEL = SCRIPT_MODEL


def process_transcript_chunks(full_text: str, chunk_size: int = 2000) -> list:
    """
    Process transcript in WORD chunks to extract key content from ALL sections.
    This prevents losing 60%+ of content due to character truncation.

    Args:
        full_text: The complete transcript text
        chunk_size: Number of words per chunk (default 2000 words ≈ 10-15 min of speech)

    Returns:
        List of text chunks for processing
    """
    words = full_text.split()
    total_words = len(words)
    chunks = []

    for i in range(0, total_words, chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append({
            "index": len(chunks),
            "start_word": i,
            "end_word": min(i + chunk_size, total_words),
            "text": chunk
        })

    print(f"  Split transcript into {len(chunks)} chunks ({chunk_size} words each)")
    return chunks


def extract_key_content_per_chunk(chunks: list) -> dict:
    """
    For each chunk, extract: key concepts, examples, steps, analogies.
    Merges all chunk results into comprehensive content.

    Returns:
        {
            "concepts": [...],      # All key concepts across transcript
            "examples": [...],      # Concrete examples mentioned
            "steps": [...],         # Process steps or sequences
            "analogies": [...],     # Metaphors and comparisons
            "quotes": [...]         # Memorable phrases
        }
    """
    all_content = {
        "concepts": [],
        "examples": [],
        "steps": [],
        "analogies": [],
        "quotes": []
    }

    extraction_prompt = """Extract structured content from this transcript section.

TEXT:
{chunk}

Return JSON with:
- concepts: array of key concepts/ideas mentioned (3-5 items)
- examples: array of concrete examples given (2-3 items)
- steps: array of process steps if any are described (up to 4)
- analogies: array of metaphors/comparisons used (1-2 items)
- quotes: array of memorable phrases worth highlighting (1-2 items)

JSON:"""

    for chunk in chunks:
        prompt = extraction_prompt.format(chunk=chunk["text"][:4000])
        try:
            response = call_ollama(prompt, model=SUMMARIZER_MODEL, timeout=TIMEOUT_MEDIUM)
        except Exception as e:
            print(f"  Chunk {chunk['index']}: Ollama error ({e})")
            continue

        # Parse JSON response
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                json_str = match.group()
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                data = json.loads(json_str)

                # Merge into all_content
                for key in all_content:
                    if key in data and isinstance(data[key], list):
                        all_content[key].extend(data[key])
        except (json.JSONDecodeError, Exception) as e:
            print(f"  Chunk {chunk['index']}: extraction error ({e})")
            continue

    # Deduplicate while preserving order
    for key in all_content:
        seen = set()
        unique = []
        for item in all_content[key]:
            item_str = str(item).lower().strip()
            if item_str not in seen and len(item_str) > 5:
                seen.add(item_str)
                unique.append(item)
        all_content[key] = unique

    print(f"  Extracted: {len(all_content['concepts'])} concepts, "
          f"{len(all_content['examples'])} examples, "
          f"{len(all_content['steps'])} steps, "
          f"{len(all_content['analogies'])} analogies")

    return all_content


def extract_narrative_structure(full_text: str) -> dict:
    """
    Identify storytelling elements for engaging NotebookLM-style content.

    Returns:
        {
            "hook": "Surprising fact or question to grab attention",
            "setup": "Problem or situation introduced",
            "tension": "Challenges or complexity that builds",
            "climax": "Key insight or breakthrough moment",
            "resolution": "What viewers should do with this knowledge"
        }
    """
    prompt = f"""Analyze this content for narrative structure to create engaging educational video.

TRANSCRIPT (first and last sections):
{full_text[:3000]}
...
{full_text[-2000:]}

Extract the storytelling elements:
- hook: What surprising fact, question, or statement can grab attention in the first 10 seconds?
- setup: What problem, situation, or context is introduced?
- tension: What challenges, complexity, or "but wait" moments build interest?
- climax: What is the key insight, breakthrough, or "aha moment"?
- resolution: What should viewers do with this knowledge? How does it help them?

Return JSON:"""

    default_structure = {
        "hook": "",
        "setup": "",
        "tension": "",
        "climax": "",
        "resolution": ""
    }

    try:
        response = call_ollama(prompt, model=SUMMARIZER_MODEL, timeout=TIMEOUT_MEDIUM)
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            json_str = match.group()
            json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
            json_str = json_str.replace("\n", " ")
            data = json.loads(json_str)
            for key in default_structure:
                if key in data and data[key]:
                    default_structure[key] = str(data[key])[:200]
            return default_structure
    except Exception as e:
        print(f"  Narrative structure extraction error: {e}")

    # Fallback: extract from transcript directly
    sentences = re.split(r'[.!?]+', full_text)
    meaningful = [s.strip() for s in sentences if len(s.strip()) > 20]

    if meaningful:
        default_structure["hook"] = meaningful[0][:150] if meaningful else ""
        default_structure["climax"] = meaningful[len(meaningful)//2][:150] if len(meaningful) > 2 else ""
        default_structure["resolution"] = meaningful[-1][:150] if meaningful else ""

    return default_structure


def deep_process_transcript(full_text: str) -> dict:
    """
    Comprehensive transcript processing using chunks and narrative analysis.
    This is the NotebookLM-style deep content extraction.

    Returns:
        {
            "chunk_content": {...},      # Extracted from all chunks
            "narrative": {...},          # Story structure
            "scene_suggestions": [...]   # Suggested scene topics based on content
        }
    """
    print(f"  Deep processing transcript ({len(full_text.split())} words)...")

    # Process in chunks
    chunks = process_transcript_chunks(full_text)
    chunk_content = extract_key_content_per_chunk(chunks)

    # Extract narrative structure
    print(f"  Analyzing narrative structure...")
    narrative = extract_narrative_structure(full_text)

    # Generate scene suggestions based on extracted content
    scene_suggestions = []

    # Scene 1: Hook/Intro from narrative
    if narrative.get("hook"):
        scene_suggestions.append({
            "type": "intro",
            "focus": "hook",
            "content": narrative["hook"]
        })

    # Middle scenes: From concepts and examples
    for i, concept in enumerate(chunk_content.get("concepts", [])[:4]):
        scene_suggestions.append({
            "type": "concept",
            "focus": concept,
            "examples": chunk_content.get("examples", [])[i:i+1] if i < len(chunk_content.get("examples", [])) else []
        })

    # If steps exist, add process scene
    if chunk_content.get("steps"):
        scene_suggestions.append({
            "type": "process",
            "focus": "steps",
            "content": chunk_content["steps"][:5]
        })

    # Conclusion from narrative resolution
    if narrative.get("resolution"):
        scene_suggestions.append({
            "type": "conclusion",
            "focus": "resolution",
            "content": narrative["resolution"]
        })

    print(f"  Generated {len(scene_suggestions)} scene suggestions")

    return {
        "chunk_content": chunk_content,
        "narrative": narrative,
        "scene_suggestions": scene_suggestions
    }
