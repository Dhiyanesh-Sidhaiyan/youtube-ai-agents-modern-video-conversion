"""
YouTube transcript fetching utilities.

Responsibility: YouTube API calls only — no LLM, no file I/O.
"""

import os
import re
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from youtube_transcript_api import YouTubeTranscriptApi


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
