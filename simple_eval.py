#!/usr/bin/env python3
"""Simple scene evaluation without external dependencies."""

import json
import subprocess
from pathlib import Path
from datetime import datetime
import os

OUTPUT_DIR = Path("output")
VIDEOS_DIR = OUTPUT_DIR / "videos"
SCRIPT_PATH = OUTPUT_DIR / "script.json"
EVAL_DIR = OUTPUT_DIR / "scene_evaluation"
EVAL_DIR.mkdir(exist_ok=True)

def find_scene_video(scene_num):
    """Find the Scene video file."""
    video_path = VIDEOS_DIR / f"scene_{scene_num}" / "480p15" / f"Scene{scene_num}.mp4"
    return video_path if video_path.exists() else None

def extract_frame(video_path, time_sec, output_image):
    """Extract single frame from video."""
    try:
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-ss", str(time_sec),
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
            "-vframes", "1", "-y", str(output_image)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0 and os.path.exists(output_image)
    except Exception as e:
        return False

def main():
    print("\n" + "═" * 70)
    print("  SCENE SCREENSHOT EXTRACTION & EVALUATION")
    print("═" * 70 + "\n")

    if not SCRIPT_PATH.exists():
        print(f"✗ Script not found")
        return

    with open(SCRIPT_PATH) as f:
        script = json.load(f)

    print(f"📋 Title: {script['title']}")
    print(f"📊 Total scenes: {len(script['scenes'])}\n")

    results = []

    for i in range(1, len(script['scenes']) + 1):
        scene = script['scenes'][i-1]
        video_path = find_scene_video(i)
        frame_image = EVAL_DIR / f"scene_{i}_frame.png"

        print(f"[Scene {i}] {scene['title'][:50]}")

        if not video_path:
            print(f"  ✗ Video not found")
            continue

        print(f"  ✓ Found video")
        print(f"  • Extracting 1-second frame...")

        if extract_frame(video_path, 1.0, frame_image):
            print(f"    ✓ Saved: {frame_image.name}")

            # Gather metrics
            narration = scene['narration_text']
            words = len(narration.split())

            result = {
                "scene": i,
                "title": scene['title'],
                "type": scene['scene_type'],
                "frame_file": frame_image.name,
                "narration_words": words,
                "narration_chars": len(narration),
                "key_concepts": len(scene.get('key_concepts', [])),
                "visual_desc": scene.get('visual_description', '')[:80]
            }
            results.append(result)

            print(f"    • Narration: {words} words")
            print(f"    • Concepts: {result['key_concepts']} items")
            print(f"    • Type: {scene['scene_type']}")
        else:
            print(f"  ✗ Frame extraction failed")

        print()

    # Summary
    print("═" * 70)
    print(f"✓ FRAMES EXTRACTED: {len(results)}/{len(script['scenes'])}")
    print(f"✓ LOCATION: {EVAL_DIR}/")
    print(f"✓ FILES: scene_N_frame.png (N=1 to {len(results)})\n")

    # Concept alignment check
    print("CONTENT QUALITY CHECK")
    print("═" * 70)

    for result in results:
        i = result['scene']
        scene = script['scenes'][i-1]
        print(f"\n[Scene {i}] {result['title']}")
        print(f"  Type: {result['type']}")
        print(f"  Words: {result['narration_words']}")
        print(f"  Concepts: {result['key_concepts']}")

        # Check text truncation
        narration = scene['narration_text']
        if narration.endswith('...'):
            print(f"  ⚠️  WARNING: Narration seems truncated")
        else:
            print(f"  ✓ Narration complete")

        # Show sample
        print(f"  Sample: {narration[:100]}...")

    # Save results
    with open(EVAL_DIR / "evaluation.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "script_title": script["title"],
            "frames_extracted": len(results),
            "total_scenes": len(script["scenes"]),
            "results": results
        }, f, indent=2)

    print(f"\n✓ Results saved: {EVAL_DIR / 'evaluation.json'}")

if __name__ == "__main__":
    main()
