"""
agents.transcript — YouTube transcript fetching and processing pipeline.

Responsibility split:
    youtube_fetcher.py      — YouTube API calls (no LLM)
    transcript_processor.py — Basic LLM summarization and concept extraction
    deep_analyzer.py        — NotebookLM-style chunk-based deep extraction

Public API (backward compatible with agents.transcript_agent):
    fetch_and_process_transcript(youtube_url, language, deep_process) -> dict
    load_transcript_file(file_path, deep_process) -> dict
"""

import json

from .youtube_fetcher import extract_video_id, fetch_transcript, group_transcript_by_minute
from .transcript_processor import summarize_transcript, extract_key_concepts
from .deep_analyzer import deep_process_transcript


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

    video_id = extract_video_id(youtube_url)
    print(f"  Video ID: {video_id}")

    print(f"  Fetching transcript (language: {language})...")
    raw_transcript = fetch_transcript(video_id, language)

    if not raw_transcript:
        raise ValueError(f"Could not fetch transcript for {video_id}")

    last_entry = raw_transcript[-1]
    duration_seconds = last_entry.start + last_entry.duration
    duration_minutes = int(duration_seconds / 60)

    full_text = " ".join([entry.text for entry in raw_transcript])
    word_count = len(full_text.split())

    print(f"  Duration: {duration_minutes} minutes")
    print(f"  Word count: {word_count}")

    segments = group_transcript_by_minute(raw_transcript)
    print(f"  Segments: {len(segments)}")

    print(f"  Summarizing transcript...")
    summary = summarize_transcript(full_text)

    print(f"  Extracting key concepts...")
    key_concepts = extract_key_concepts(full_text)
    print(f"  Key concepts: {key_concepts}")

    deep_content = None
    if deep_process and word_count > 500:
        print(f"  [NotebookLM-style] Deep content extraction...")
        deep_content = deep_process_transcript(full_text)

        if deep_content and deep_content.get("chunk_content"):
            chunk_concepts = deep_content["chunk_content"].get("concepts", [])
            existing = set(c.lower() for c in key_concepts)
            for c in chunk_concepts:
                if c.lower() not in existing:
                    key_concepts.append(c)
                    existing.add(c.lower())
            key_concepts = key_concepts[:12]

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
            if deep_process and "deep_content" not in data and data.get("full_text"):
                print(f"  [NotebookLM-style] Adding deep content extraction...")
                data["deep_content"] = deep_process_transcript(data["full_text"])
            return data
    except json.JSONDecodeError:
        pass

    # Plain text transcript
    full_text = content
    word_count = len(full_text.split())
    duration_minutes = max(1, word_count // 150)  # ~150 words/min for speech

    print(f"  Word count: {word_count}")
    print(f"  Estimated duration: {duration_minutes} minutes")

    print(f"  Summarizing...")
    summary = summarize_transcript(full_text)

    print(f"  Extracting key concepts...")
    key_concepts = extract_key_concepts(full_text)

    deep_content = None
    if deep_process and word_count > 500:
        print(f"  [NotebookLM-style] Deep content extraction...")
        deep_content = deep_process_transcript(full_text)

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


__all__ = [
    "fetch_and_process_transcript",
    "load_transcript_file",
    "extract_video_id",
    "fetch_transcript",
    "summarize_transcript",
    "extract_key_concepts",
    "deep_process_transcript",
]
