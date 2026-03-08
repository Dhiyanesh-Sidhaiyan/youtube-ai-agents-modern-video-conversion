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


def fetch_and_process_transcript(youtube_url: str, language: str = "en") -> dict:
    """
    Fetch YouTube transcript and preprocess for script generation.

    Returns:
        {
            "video_id": str,
            "duration_minutes": int,
            "word_count": int,
            "segments": [...],
            "full_text": str,
            "summary": str,
            "key_concepts": [str]
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

    return {
        "video_id": video_id,
        "duration_minutes": duration_minutes,
        "word_count": word_count,
        "segments": segments,
        "full_text": full_text,
        "summary": summary,
        "key_concepts": key_concepts
    }


def load_transcript_file(file_path: str) -> dict:
    """Load transcript from a local file (transcript.log or JSON)."""
    print(f"\n[Transcript Agent] Loading: {file_path}")

    with open(file_path, 'r') as f:
        content = f.read()

    # Try JSON first
    try:
        data = json.loads(content)
        if "summary" in data and "key_concepts" in data:
            return data  # Already processed
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

    return {
        "video_id": "local_file",
        "duration_minutes": duration_minutes,
        "word_count": word_count,
        "segments": [],
        "full_text": full_text,
        "summary": summary,
        "key_concepts": key_concepts
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
