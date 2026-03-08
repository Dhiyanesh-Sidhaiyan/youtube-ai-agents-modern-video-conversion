from youtube_transcript_api import YouTubeTranscriptApi
import re
import sys


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


def get_transcript(video_id: str, language: str = 'en') -> list:
    """Fetch transcript for a YouTube video."""
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=[language])
        return list(transcript)
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return []


def main():
    # Example video ID - replace with your own
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    if len(sys.argv) > 1:
        video_url = sys.argv[1]

    video_id = extract_video_id(video_url)
    print(f"Fetching transcript for video ID: {video_id}\n")

    transcript = get_transcript(video_id)

    if transcript:
        print("=" * 50)
        print("TRANSCRIPT")
        print("=" * 50)
        for line in transcript:
            timestamp = f"[{line.start:.1f}s]"
            print(f"{timestamp:12} {line.text}")

        print("\n" + "=" * 50)
        print(f"Total lines: {len(transcript)}")
    else:
        print("No transcript available for this video.")


if __name__ == "__main__":
    main()
