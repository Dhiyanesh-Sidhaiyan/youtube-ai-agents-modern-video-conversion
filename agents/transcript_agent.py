"""
Agent 0: Transcript Agent
Fetches YouTube transcripts and preprocesses them for script generation.
Integrates with get_transcript.py and adds summarization via LLM.
"""

import json
import os
import re
import sys
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_transcript_api import YouTubeTranscriptApi


OLLAMA_URL = "http://localhost:11434/api/generate"
SUMMARIZER_MODEL = "phi4"
OLLAMA_TIMEOUT = 120


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from YouTube URL or return as-is if already an ID."""
    patterns = [
        r'(?:youtube\.com/watch\?v=)([^&]+)',
        r'(?:youtu\.be/)([^?]+)',
        r'(?:youtube\.com/embed/)([^?]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    return url_or_id  # Assume it's already a video ID


def fetch_transcript(video_id: str, language: str = 'en') -> list:
    """Fetch transcript for a YouTube video."""
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=[language])
        return list(transcript)
    except Exception as e:
        print(f"  Error fetching transcript: {e}")
        return []


def group_transcript_by_minute(transcript: list) -> list:
    """Group transcript entries by minute for easier processing."""
    if not transcript:
        return []

    grouped = []
    current_minute = -1
    current_text = []

    for entry in transcript:
        minute = int(entry.start // 60)
        if minute != current_minute:
            if current_text:
                grouped.append({
                    "minute": current_minute,
                    "start": current_minute * 60,
                    "end": (current_minute + 1) * 60,
                    "text": " ".join(current_text)
                })
            current_minute = minute
            current_text = [entry.text]
        else:
            current_text.append(entry.text)

    # Add last group
    if current_text:
        grouped.append({
            "minute": current_minute,
            "start": current_minute * 60,
            "end": (current_minute + 1) * 60,
            "text": " ".join(current_text)
        })

    return grouped


def call_ollama(prompt: str, model: str = SUMMARIZER_MODEL) -> str:
    """Call Ollama LLM for summarization."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 2000}
            },
            timeout=OLLAMA_TIMEOUT
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"  Ollama error: {e}")
        return ""


def summarize_transcript(full_text: str) -> str:
    """Use LLM to create a concise summary of the transcript."""
    prompt = f"""Summarize the following YouTube video transcript into a concise abstract (150-250 words).
Focus on:
1. The main topic and purpose
2. Key concepts and ideas presented
3. Important examples or demonstrations
4. Conclusions or takeaways

TRANSCRIPT:
{full_text[:8000]}  # Limit to avoid token overflow

SUMMARY (150-250 words):"""

    summary = call_ollama(prompt)
    return summary if summary else full_text[:500]  # Fallback to truncated text


def extract_key_concepts(full_text: str) -> list:
    """Use LLM to extract key concepts from the transcript."""
    prompt = f"""Extract 5-8 key concepts or topics from this YouTube video transcript.
Return ONLY a JSON array of strings, no explanation.

TRANSCRIPT:
{full_text[:6000]}

KEY CONCEPTS (JSON array):"""

    response = call_ollama(prompt)

    # Try to parse JSON array
    try:
        # Find JSON array in response
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            concepts = json.loads(match.group())
            return concepts[:8]  # Limit to 8
    except json.JSONDecodeError:
        pass

    # Fallback: extract quoted strings
    concepts = re.findall(r'"([^"]+)"', response)
    if concepts:
        return concepts[:8]

    # Last resort: return generic concepts
    return ["Main Topic", "Key Idea", "Example", "Conclusion"]


# ─── Chunk-Based Processing (NotebookLM-style Deep Content Extraction) ──────

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
        response = call_ollama(prompt)

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

    response = call_ollama(prompt)

    default_structure = {
        "hook": "",
        "setup": "",
        "tension": "",
        "climax": "",
        "resolution": ""
    }

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            json_str = match.group()
            json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
            json_str = json_str.replace("\n", " ")
            data = json.loads(json_str)
            # Merge with defaults
            for key in default_structure:
                if key in data and data[key]:
                    default_structure[key] = str(data[key])[:200]
            return default_structure
    except (json.JSONDecodeError, Exception) as e:
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


def fetch_and_process_transcript(youtube_url: str, language: str = "en", deep_process: bool = True) -> dict:
    """
    Fetch YouTube transcript and preprocess for script generation.
    Uses NotebookLM-style deep content extraction for better quality.

    Args:
        youtube_url: YouTube URL or video ID
        language: Transcript language code
        deep_process: If True, uses chunk-based extraction for full coverage

    Returns:
        {
            "video_id": str,
            "duration_minutes": int,
            "word_count": int,
            "segments": [...],
            "full_text": str,
            "summary": str,
            "key_concepts": [str],
            "deep_content": {...}  # NotebookLM-style extracted content
        }
    """
    print(f"\n[Transcript Agent] Processing: {youtube_url}")

    # Extract video ID
    video_id = extract_video_id(youtube_url)
    print(f"  Video ID: {video_id}")

    # Fetch transcript
    print(f"  Fetching transcript (language: {language})...")
    raw_transcript = fetch_transcript(video_id, language)

    if not raw_transcript:
        raise ValueError(f"Could not fetch transcript for {video_id}")

    # Calculate duration
    last_entry = raw_transcript[-1]
    duration_seconds = last_entry.start + last_entry.duration
    duration_minutes = int(duration_seconds / 60)

    # Build full text
    full_text = " ".join([entry.text for entry in raw_transcript])
    word_count = len(full_text.split())

    print(f"  Duration: {duration_minutes} minutes")
    print(f"  Word count: {word_count}")

    # Group by minute
    segments = group_transcript_by_minute(raw_transcript)
    print(f"  Segments: {len(segments)}")

    # Summarize using LLM
    print(f"  Summarizing transcript...")
    summary = summarize_transcript(full_text)

    # Extract key concepts
    print(f"  Extracting key concepts...")
    key_concepts = extract_key_concepts(full_text)
    print(f"  Key concepts: {key_concepts}")

    # Deep content extraction (NotebookLM-style)
    deep_content = None
    if deep_process and word_count > 500:
        print(f"  [NotebookLM-style] Deep content extraction...")
        deep_content = deep_process_transcript(full_text)

        # Enhance key_concepts with chunk-extracted concepts
        if deep_content and deep_content.get("chunk_content"):
            chunk_concepts = deep_content["chunk_content"].get("concepts", [])
            # Merge unique concepts
            existing = set(c.lower() for c in key_concepts)
            for c in chunk_concepts:
                if c.lower() not in existing:
                    key_concepts.append(c)
                    existing.add(c.lower())
            key_concepts = key_concepts[:12]  # Limit to 12

    return {
        "video_id": video_id,
        "duration_minutes": duration_minutes,
        "word_count": word_count,
        "segments": segments,
        "full_text": full_text,
        "summary": summary,
        "key_concepts": key_concepts,
        "deep_content": deep_content
    }


def load_transcript_file(file_path: str, deep_process: bool = True) -> dict:
    """
    Load transcript from a local file (transcript.log or JSON).
    Uses NotebookLM-style deep content extraction for better quality.
    """
    print(f"\n[Transcript Agent] Loading: {file_path}")

    with open(file_path, 'r') as f:
        content = f.read()

    # Try JSON first
    try:
        data = json.loads(content)
        if "summary" in data and "key_concepts" in data:
            # Already processed - but add deep content if missing
            if deep_process and "deep_content" not in data and data.get("full_text"):
                print(f"  [NotebookLM-style] Adding deep content extraction...")
                data["deep_content"] = deep_process_transcript(data["full_text"])
            return data
    except json.JSONDecodeError:
        pass

    # Plain text transcript
    full_text = content
    word_count = len(full_text.split())

    # Estimate duration (assuming ~150 words per minute for speech)
    duration_minutes = max(1, word_count // 150)

    print(f"  Word count: {word_count}")
    print(f"  Estimated duration: {duration_minutes} minutes")

    # Summarize
    print(f"  Summarizing...")
    summary = summarize_transcript(full_text)

    # Extract concepts
    print(f"  Extracting key concepts...")
    key_concepts = extract_key_concepts(full_text)

    # Deep content extraction (NotebookLM-style)
    deep_content = None
    if deep_process and word_count > 500:
        print(f"  [NotebookLM-style] Deep content extraction...")
        deep_content = deep_process_transcript(full_text)

        # Enhance key_concepts with chunk-extracted concepts
        if deep_content and deep_content.get("chunk_content"):
            chunk_concepts = deep_content["chunk_content"].get("concepts", [])
            existing = set(c.lower() for c in key_concepts)
            for c in chunk_concepts:
                if c.lower() not in existing:
                    key_concepts.append(c)
                    existing.add(c.lower())
            key_concepts = key_concepts[:12]

    return {
        "video_id": "local_file",
        "duration_minutes": duration_minutes,
        "word_count": word_count,
        "segments": [],
        "full_text": full_text,
        "summary": summary,
        "key_concepts": key_concepts,
        "deep_content": deep_content
    }


if __name__ == "__main__":
    # Test with a YouTube URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
        lang = sys.argv[2] if len(sys.argv) > 2 else "en"

        if url.startswith("http"):
            result = fetch_and_process_transcript(url, lang)
        else:
            result = load_transcript_file(url)

        print("\n" + "=" * 60)
        print("RESULT:")
        print(f"  Duration: {result['duration_minutes']} min")
        print(f"  Words: {result['word_count']}")
        print(f"  Summary: {result['summary'][:200]}...")
        print(f"  Concepts: {result['key_concepts']}")
    else:
        print("Usage: python transcript_agent.py <youtube_url_or_file> [language]")
