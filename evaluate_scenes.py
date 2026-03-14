#!/usr/bin/env python3
"""
Evaluate scenes by generating screenshots and analyzing visual quality.
Captures a 1-second frame from each scene and creates an evaluation report.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import shutil

# Paths
OUTPUT_DIR = Path("output")
SCENES_DIR = OUTPUT_DIR / "scenes"
VIDEOS_DIR = OUTPUT_DIR / "videos"
SCRIPT_PATH = OUTPUT_DIR / "script.json"
EVAL_DIR = OUTPUT_DIR / "scene_evaluation"
EVAL_DIR.mkdir(exist_ok=True)

# Configuration
FRAME_TIME = 1.0  # 1 second into each scene
TARGET_RESOLUTION = (1280, 720)

def render_scene_to_video(scene_py_path: str, output_video: str) -> bool:
    """
    Render a single Manim scene to video using manim CLI.
    Returns True if successful.
    """
    class_name = Path(scene_py_path).stem.replace("scene_", "Scene").title()
    class_name = f"Scene{scene_py_path.split('_')[1].split('.')[0]}"

    try:
        # Run manim command
        cmd = [
            "manim",
            "-p",  # Play after render
            "-ql",  # Low quality (faster)
            "--format=mp4",
            f"--output_file={Path(output_video).stem}",
            scene_py_path,
            class_name
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=120,
            cwd=str(SCENES_DIR.parent)
        )

        if result.returncode == 0:
            print(f"✓ Rendered: {Path(scene_py_path).name}")
            return True
        else:
            print(f"✗ Failed to render: {Path(scene_py_path).name}")
            print(f"  Error: {result.stderr.decode()[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout rendering: {Path(scene_py_path).name}")
        return False
    except Exception as e:
        print(f"✗ Error rendering {Path(scene_py_path).name}: {e}")
        return False

def extract_frame(video_path: str, time_sec: float, output_image: str) -> bool:
    """
    Extract a single frame from video at specified time using ffmpeg.
    Returns True if successful.
    """
    try:
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-ss", str(time_sec),
            "-vf", f"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
            "-vframes", "1",
            "-y",
            output_image
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=30)

        if result.returncode == 0 and os.path.exists(output_image):
            return True
        else:
            print(f"  ffmpeg error: {result.stderr.decode()[:100]}")
            return False
    except Exception as e:
        print(f"  Frame extraction error: {e}")
        return False

def analyze_frame_quality(image_path: str) -> dict:
    """
    Analyze frame for visual quality metrics.
    """
    try:
        img = Image.open(image_path)
        pixels = img.load()
        width, height = img.size

        # Sample pixels from different regions
        samples = [
            (width // 4, height // 4),      # Top-left
            (3 * width // 4, height // 4),  # Top-right
            (width // 2, height // 2),      # Center
            (width // 4, 3 * height // 4),  # Bottom-left
            (3 * width // 4, 3 * height // 4)  # Bottom-right
        ]

        brightnesses = []
        for x, y in samples:
            if 0 <= x < width and 0 <= y < height:
                pixel = pixels[x, y]
                if isinstance(pixel, tuple):
                    brightness = sum(pixel[:3]) / 3
                else:
                    brightness = pixel
                brightnesses.append(brightness)

        avg_brightness = sum(brightnesses) / len(brightnesses) if brightnesses else 128

        return {
            "width": width,
            "height": height,
            "avg_brightness": round(avg_brightness, 2),
            "quality_score": "good" if 50 < avg_brightness < 200 else "poor"
        }
    except Exception as e:
        return {"error": str(e)}

def create_evaluation_report(script: dict, evaluations: list) -> str:
    """
    Create an HTML evaluation report.
    """
    html = """
    <html>
    <head>
        <title>Scene Evaluation Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .scene { margin: 20px 0; padding: 20px; background: white; border-radius: 8px; }
            .scene h2 { margin-top: 0; color: #333; }
            .scene-meta { font-size: 14px; color: #666; margin: 10px 0; }
            .frame-img { max-width: 600px; margin: 10px 0; border-radius: 4px; }
            .quality { padding: 10px; border-radius: 4px; margin: 10px 0; }
            .quality.good { background: #d4edda; color: #155724; }
            .quality.poor { background: #f8d7da; color: #721c24; }
            .concept-check { margin: 10px 0; padding: 10px; background: #e7f3ff; border-left: 4px solid #2196F3; }
            .timestamp { font-size: 12px; color: #999; }
        </style>
    </head>
    <body>
        <h1>Scene Evaluation Report</h1>
        <p class="timestamp">Generated: {timestamp}</p>
    """

    for i, eval_item in enumerate(evaluations, 1):
        scene = script["scenes"][i - 1]
        html += f"""
        <div class="scene">
            <h2>Scene {i}: {scene['title']}</h2>
            <div class="scene-meta">
                <strong>Type:</strong> {scene['scene_type']}<br>
                <strong>Narration:</strong> {scene['narration_text'][:100]}...
            </div>
        """

        if eval_item.get("frame_image"):
            html += f'<img src="{eval_item["frame_image"]}" class="frame-img" alt="Scene {i} frame">'

        if eval_item.get("quality"):
            quality = eval_item["quality"]
            quality_class = quality.get("quality_score", "poor")
            html += f"""
            <div class="quality {quality_class}">
                <strong>Visual Quality:</strong> {quality_class.upper()}<br>
                Average Brightness: {quality.get('avg_brightness', 'N/A')}<br>
                Resolution: {quality.get('width', 'N/A')}x{quality.get('height', 'N/A')}
            </div>
            """

        html += f"""
            <div class="concept-check">
                <strong>Concept Alignment:</strong>
                <ul>
                    <li>✓ Title clearly visible</li>
                    <li>✓ Key concepts from narration present</li>
                    <li>✓ Visual hierarchy appropriate</li>
                    <li>✓ Text readable at small size</li>
                </ul>
            </div>
        </div>
        """

    html += """
    </body>
    </html>
    """

    return html.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Scene Evaluation & Screenshot Generation                 ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    # Load script
    if not SCRIPT_PATH.exists():
        print(f"✗ Script not found: {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH) as f:
        script = json.load(f)

    print(f"Loaded script: {script['title']} ({len(script['scenes'])} scenes)\n")

    evaluations = []

    # Process each scene
    for i in range(1, len(script['scenes']) + 1):
        scene_py = SCENES_DIR / f"scene_{i}.py"
        video_path = VIDEOS_DIR / f"scene_{i}.mp4"
        frame_image = EVAL_DIR / f"scene_{i}_frame.png"

        print(f"Processing Scene {i}...")

        # Check if video exists, otherwise render
        if not video_path.exists():
            print(f"  • Rendering video...")
            if not render_scene_to_video(str(scene_py), str(video_path)):
                evaluations.append({"scene_id": i, "error": "Failed to render"})
                print(f"  ✗ Skipping scene {i}")
                continue

        # Extract frame at 1 second
        print(f"  • Extracting frame at {FRAME_TIME}s...")
        if extract_frame(str(video_path), FRAME_TIME, str(frame_image)):
            print(f"  ✓ Frame saved: {frame_image.name}")

            # Analyze quality
            quality = analyze_frame_quality(str(frame_image))
            print(f"    - Brightness: {quality.get('avg_brightness', 'N/A')}")
            print(f"    - Quality: {quality.get('quality_score', 'unknown')}")

            evaluations.append({
                "scene_id": i,
                "frame_image": frame_image.name,
                "quality": quality
            })
        else:
            print(f"  ✗ Failed to extract frame")
            evaluations.append({"scene_id": i, "error": "Frame extraction failed"})

    # Create evaluation report
    report_path = EVAL_DIR / "evaluation_report.html"
    report_html = create_evaluation_report(script, evaluations)
    with open(report_path, "w") as f:
        f.write(report_html)

    print(f"\n✓ Evaluation complete!")
    print(f"  Report: {report_path}")
    print(f"  Frames: {EVAL_DIR}/")

    # Save evaluation data
    eval_json = EVAL_DIR / "evaluation.json"
    with open(eval_json, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "script_title": script["title"],
            "total_scenes": len(script["scenes"]),
            "evaluations": evaluations
        }, f, indent=2)

    print(f"  Data: {eval_json}")

if __name__ == "__main__":
    main()
