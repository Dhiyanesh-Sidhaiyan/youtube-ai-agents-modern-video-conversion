#!/usr/bin/env python3
"""
Quick scene evaluation - extracts frames from existing videos and analyzes them.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image
import os

OUTPUT_DIR = Path("output")
VIDEOS_DIR = OUTPUT_DIR / "videos"
SCRIPT_PATH = OUTPUT_DIR / "script.json"
EVAL_DIR = OUTPUT_DIR / "scene_evaluation"
EVAL_DIR.mkdir(exist_ok=True)

def extract_frame(video_path: str, time_sec: float, output_image: str) -> bool:
    """Extract frame from video using ffmpeg."""
    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-ss", str(time_sec),
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
            "-vframes", "1", "-y", output_image
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0 and os.path.exists(output_image)
    except Exception as e:
        print(f"Error extracting frame: {e}")
        return False

def analyze_image(image_path: str) -> dict:
    """Analyze image quality."""
    try:
        img = Image.open(image_path)
        pixels = img.load()
        w, h = img.size

        # Sample brightness
        samples = [(w//4, h//4), (3*w//4, h//4), (w//2, h//2), (w//4, 3*h//4), (3*w//4, 3*h//4)]
        brightnesses = []
        for x, y in samples:
            if 0 <= x < w and 0 <= y < h:
                p = pixels[x, y]
                b = sum(p[:3])/3 if isinstance(p, tuple) else p
                brightnesses.append(b)

        avg = sum(brightnesses)/len(brightnesses) if brightnesses else 128
        return {
            "brightness": round(avg, 1),
            "quality": "✓ GOOD" if 50 < avg < 200 else "⚠ POOR"
        }
    except:
        return {"error": "Analysis failed"}

def main():
    print("\n" + "═"*60)
    print("  SCENE EVALUATION - Frame Analysis")
    print("═"*60 + "\n")

    if not SCRIPT_PATH.exists():
        print(f"✗ Script not found: {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH) as f:
        script = json.load(f)

    print(f"Script: {script['title']}")
    print(f"Scenes: {len(script['scenes'])}\n")

    results = []

    for i in range(1, len(script['scenes']) + 1):
        scene = script['scenes'][i-1]
        video_path = VIDEOS_DIR / f"scene_{i}.mp4"
        frame_image = EVAL_DIR / f"scene_{i}_frame.png"

        print(f"Scene {i}: {scene['title']}")

        if not video_path.exists():
            print(f"  ✗ Video not found: {video_path.name}")
            continue

        print(f"  • Extracting frame...")
        if extract_frame(str(video_path), 1.0, str(frame_image)):
            print(f"    ✓ Saved: {frame_image.name}")

            # Analyze
            analysis = analyze_image(str(frame_image))
            print(f"    • Brightness: {analysis.get('brightness', 'N/A')}")
            print(f"    • Quality: {analysis.get('quality', '?')}")

            # Text content check
            narration = scene['narration_text']
            print(f"    • Content: {len(narration)} chars, {len(narration.split())} words")

            results.append({
                "scene": i,
                "title": scene['title'],
                "type": scene['scene_type'],
                "frame": frame_image.name,
                "analysis": analysis,
                "narration_length": len(narration)
            })
        else:
            print(f"  ✗ Frame extraction failed")

        print()

    # Summary report
    print("═"*60)
    print("SUMMARY")
    print("═"*60)
    print(f"Processed: {len(results)}/{len(script['scenes'])} scenes")
    print(f"Frames saved to: {EVAL_DIR}/\n")

    # Save JSON
    with open(EVAL_DIR / "evaluation_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "script": script['title'],
            "results": results
        }, f, indent=2)

    print(f"Results saved: evaluation_results.json")
    print()

if __name__ == "__main__":
    main()
