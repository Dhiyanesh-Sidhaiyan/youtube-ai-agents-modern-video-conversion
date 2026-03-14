#!/usr/bin/env python3
"""
Final scene evaluation - extracts frames from Manim-generated videos and analyzes them.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = Path("output")
VIDEOS_DIR = OUTPUT_DIR / "videos"
SCRIPT_PATH = OUTPUT_DIR / "script.json"
EVAL_DIR = OUTPUT_DIR / "scene_evaluation"
EVAL_DIR.mkdir(exist_ok=True)

def find_scene_video(scene_num: int) -> Path:
    """Find the Scene video file for a given number."""
    class_name = f"Scene{scene_num}"
    video_path = VIDEOS_DIR / f"scene_{scene_num}" / "480p15" / f"{class_name}.mp4"
    return video_path if video_path.exists() else None

def extract_frame(video_path, time_sec, output_image) -> bool:
    """Extract single frame from video at given time."""
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
        print(f"  Error: {e}")
        return False

def analyze_image(image_path) -> dict:
    """Analyze image brightness and quality."""
    try:
        img = Image.open(image_path)
        pixels = img.load()
        w, h = img.size

        # Sample from corners and center
        samples = [
            (w//4, h//4), (3*w//4, h//4), (w//2, h//2),
            (w//4, 3*h//4), (3*w//4, 3*h//4)
        ]

        brightnesses = []
        for x, y in samples:
            if 0 <= x < w and 0 <= y < h:
                p = pixels[x, y]
                if isinstance(p, tuple):
                    b = sum(p[:3]) / 3
                else:
                    b = p
                brightnesses.append(b)

        avg_brightness = sum(brightnesses) / len(brightnesses) if brightnesses else 128

        return {
            "brightness": round(avg_brightness, 1),
            "quality": "GOOD" if 50 < avg_brightness < 200 else "LOW",
            "resolution": f"{w}x{h}"
        }
    except Exception as e:
        return {"error": str(e)}

def create_comparison_image(frames, output_path) -> None:
    """Create a comparison image showing all scene frames."""
    try:
        # Create grid (2 rows, 3 cols for 5 scenes)
        grid_width = 1280 * 2
        grid_height = 720 * 2 + 100  # Extra space for captions
        grid = Image.new("RGB", (grid_width, grid_height), color=(20, 20, 30))
        draw = ImageDraw.Draw(grid)

        # Try to find a font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        except:
            font = ImageFont.load_default()

        positions = [
            (0, 0), (1280, 0),
            (0, 720), (1280, 720),
            (640, 1440)  # Fifth one centered at bottom
        ]

        for i, (frame_info, pos) in enumerate(zip(frames, positions)):
            if frame_info.get("frame_path") and os.path.exists(frame_info["frame_path"]):
                frame_img = Image.open(frame_info["frame_path"])
                frame_img = frame_img.resize((1280, 720))
                grid.paste(frame_img, pos)

                # Add title
                scene_num = frame_info.get("scene", "?")
                quality = frame_info.get("analysis", {}).get("quality", "?")
                text = f"Scene {scene_num} ({quality})"
                draw.text((pos[0] + 10, pos[1] + 10), text, fill=(255, 255, 0), font=font)

        grid.save(output_path)
        print(f"\n✓ Comparison image saved: {Path(output_path).name}")
    except Exception as e:
        print(f"Could not create comparison image: {e}")

def main():
    print("\n" + "═" * 70)
    print("  SCENE EVALUATION & SCREENSHOT GENERATION")
    print("═" * 70 + "\n")

    if not SCRIPT_PATH.exists():
        print(f"✗ Script not found: {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH) as f:
        script = json.load(f)

    print(f"📋 Script: {script['title']}")
    print(f"📊 Scenes: {len(script['scenes'])}\n")

    results = []
    frames = []

    for i in range(1, len(script['scenes']) + 1):
        scene = script['scenes'][i-1]
        video_path = find_scene_video(i)
        frame_image = EVAL_DIR / f"scene_{i}_frame_1sec.png"

        print(f"Scene {i}: {scene['title'][:50]}")

        if not video_path:
            print(f"  ✗ Video not found")
            continue

        print(f"  ✓ Found video: {video_path.name}")
        print(f"  • Extracting frame at 1 second...")

        if extract_frame(video_path, 1.0, frame_image):
            print(f"    ✓ Saved: {frame_image.name}")

            # Analyze
            analysis = analyze_image(frame_image)
            print(f"    • Quality: {analysis.get('quality')} (brightness: {analysis.get('brightness')})")
            print(f"    • Resolution: {analysis.get('resolution')}")

            # Content metrics
            narration = scene['narration_text']
            word_count = len(narration.split())
            print(f"    • Narration: {word_count} words, {len(narration)} chars")

            # Concept alignment check
            concepts = scene.get('key_concepts', [])
            print(f"    • Key concepts: {len(concepts)} items")

            frame_info = {
                "scene": i,
                "title": scene['title'],
                "type": scene['scene_type'],
                "frame_path": str(frame_image),
                "analysis": analysis,
                "narration_words": word_count,
                "concepts": len(concepts)
            }
            results.append(frame_info)
            frames.append(frame_info)

        print()

    # Create comparison grid
    if frames:
        grid_path = EVAL_DIR / "scene_comparison.png"
        create_comparison_image(frames, grid_path)

    # Summary
    print("═" * 70)
    print("EVALUATION SUMMARY")
    print("═" * 70)
    print(f"✓ Extracted frames: {len(results)}/{len(script['scenes'])} scenes")

    good_quality = sum(1 for r in results if r.get('analysis', {}).get('quality') == 'GOOD')
    print(f"✓ Good quality frames: {good_quality}/{len(results)}")

    avg_words = sum(r.get('narration_words', 0) for r in results) / len(results) if results else 0
    print(f"✓ Average narration: {avg_words:.0f} words per scene")

    print(f"\n📁 Output directory: {EVAL_DIR}/")
    print(f"📊 Frames saved as: scene_N_frame_1sec.png")
    print(f"🖼️  Comparison grid: scene_comparison.png\n")

    # Save detailed results
    results_file = EVAL_DIR / "evaluation_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "script_title": script["title"],
            "total_scenes": len(script["scenes"]),
            "frames_extracted": len(results),
            "results": results
        }, f, indent=2)

    print(f"✓ Results saved: {results_file.name}\n")

    # Print text content check
    print("TEXT CONTENT VERIFICATION")
    print("═" * 70)
    for i, result in enumerate(results, 1):
        print(f"\nScene {i}: {result['title']}")
        scene = script['scenes'][i-1]
        narration = scene['narration_text']
        print(f"  Narration: {narration[:80]}...")
        if scene.get('key_concepts'):
            print(f"  Concepts: {', '.join(scene['key_concepts'][:2])}...")

if __name__ == "__main__":
    main()
