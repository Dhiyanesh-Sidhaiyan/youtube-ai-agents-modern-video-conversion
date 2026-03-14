"""Frame extraction from video files using ffmpeg."""

import os
import subprocess
import tempfile

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def extract_frames(mp4_path: str, count: int = 10) -> list:
    """Extract sample frames from video using ffmpeg."""
    if not os.path.exists(mp4_path):
        return []

    frames = []
    with tempfile.TemporaryDirectory() as tmpdir:
        # Get video duration
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            mp4_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            duration = float(result.stdout.strip())
        except ValueError:
            duration = 10.0

        # Extract frames at regular intervals
        interval = duration / (count + 1)
        for i in range(count):
            timestamp = interval * (i + 1)
            frame_path = os.path.join(tmpdir, f"frame_{i:03d}.png")

            cmd = [
                "ffmpeg", "-y", "-v", "quiet",
                "-ss", str(timestamp),
                "-i", mp4_path,
                "-vframes", "1",
                "-f", "image2",
                frame_path
            ]
            subprocess.run(cmd, capture_output=True)

            if os.path.exists(frame_path) and HAS_PIL:
                try:
                    img = Image.open(frame_path)
                    frames.append((i, timestamp, img.copy()))
                    img.close()
                except Exception:
                    pass

    return frames
