#!/usr/bin/env python3
"""
Unified Scene Evaluation CLI

Replaces: evaluate_scenes.py, eval_scenes_final.py, simple_eval.py, quick_eval.py

Usage:
    python evaluation/evaluate.py                  # default: quick mode
    python evaluation/evaluate.py --mode quick     # frame extraction + brightness check
    python evaluation/evaluate.py --mode full      # quick + HTML report + comparison grid
    python evaluation/evaluate.py --script path/to/script.json
    python evaluation/evaluate.py --output path/to/output/dir
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ─── Defaults ────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("output")
SCRIPT_PATH = OUTPUT_DIR / "script.json"
EVAL_DIR = OUTPUT_DIR / "scene_evaluation"

FRAME_TIME = 1.0  # seconds into each scene to capture


# ─── Video Discovery ──────────────────────────────────────────────────────────

def find_scene_video(scene_num: int, output_dir: Path) -> Path | None:
    """Find rendered MP4 for a scene by checking common Manim output locations."""
    class_name = f"Scene{scene_num}"
    candidates = [
        # Manim low-quality output
        output_dir / "videos" / f"scene_{scene_num}" / "480p15" / f"{class_name}.mp4",
        output_dir / "videos" / f"scene_{scene_num}" / "720p30" / f"{class_name}.mp4",
        output_dir / "videos" / f"{class_name}.mp4",
        output_dir / f"scene_{scene_num}" / "480p15" / f"{class_name}.mp4",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


# ─── Frame Extraction ─────────────────────────────────────────────────────────

def extract_frame(video_path: Path, time_sec: float, output_image: Path) -> bool:
    """Extract a single frame from video at the given time using ffmpeg."""
    try:
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-ss", str(time_sec),
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
                   "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
            "-vframes", "1", "-y", str(output_image),
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0 and output_image.exists()
    except Exception as e:
        print(f"  Frame extraction error: {e}")
        return False


# ─── Image Analysis ───────────────────────────────────────────────────────────

def analyze_image(image_path: Path) -> dict:
    """Sample brightness at 5 points; return quality assessment."""
    try:
        from PIL import Image
        img = Image.open(image_path)
        pixels = img.load()
        w, h = img.size

        sample_coords = [
            (w // 4, h // 4), (3 * w // 4, h // 4), (w // 2, h // 2),
            (w // 4, 3 * h // 4), (3 * w // 4, 3 * h // 4),
        ]
        brightnesses = []
        for x, y in sample_coords:
            if 0 <= x < w and 0 <= y < h:
                p = pixels[x, y]
                b = sum(p[:3]) / 3 if isinstance(p, tuple) else float(p)
                brightnesses.append(b)

        avg = sum(brightnesses) / len(brightnesses) if brightnesses else 128.0
        return {
            "brightness": round(avg, 1),
            "resolution": f"{w}x{h}",
            "quality": "GOOD" if 50 < avg < 200 else "LOW",
        }
    except ImportError:
        return {"error": "Pillow not installed (pip install Pillow)"}
    except Exception as e:
        return {"error": str(e)}


# ─── Comparison Grid (full mode only) ────────────────────────────────────────

def create_comparison_grid(frames: list[dict], output_path: Path) -> None:
    """Create a 2-column grid image showing all scene frames."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        cols = 2
        cell_w, cell_h = 640, 360
        rows = (len(frames) + cols - 1) // cols
        grid = Image.new("RGB", (cols * cell_w, rows * cell_h), color=(20, 20, 30))
        draw = ImageDraw.Draw(grid)

        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        except Exception:
            font = ImageFont.load_default()

        for idx, frame_info in enumerate(frames):
            row, col = divmod(idx, cols)
            x, y = col * cell_w, row * cell_h

            frame_path = frame_info.get("frame_path")
            if frame_path and os.path.exists(frame_path):
                cell = Image.open(frame_path).resize((cell_w, cell_h))
                grid.paste(cell, (x, y))

            label = f"Scene {frame_info.get('scene', '?')} — {frame_info.get('quality', '?')}"
            draw.text((x + 6, y + 6), label, fill=(255, 255, 0), font=font)

        grid.save(output_path)
        print(f"  Comparison grid saved: {output_path.name}")
    except ImportError:
        print("  Skipping comparison grid (Pillow not installed)")
    except Exception as e:
        print(f"  Could not create comparison grid: {e}")


# ─── HTML Report (full mode only) ────────────────────────────────────────────

def create_html_report(script: dict, results: list[dict], output_path: Path) -> None:
    """Write a simple HTML evaluation report."""
    rows = ""
    for r in results:
        quality = r.get("analysis", {}).get("quality", "N/A")
        color = "#d4edda" if quality == "GOOD" else "#f8d7da"
        frame_tag = ""
        if r.get("frame_path") and os.path.exists(r["frame_path"]):
            rel = os.path.relpath(r["frame_path"], output_path.parent)
            frame_tag = f'<img src="{rel}" style="max-width:480px;border-radius:4px;">'
        rows += f"""
        <div style="background:white;padding:16px;margin:12px 0;border-radius:6px;">
          <h3>Scene {r['scene']}: {r['title']}</h3>
          <p><b>Type:</b> {r['type']} &nbsp; <b>Narration:</b> {r['narration_words']} words</p>
          <div style="background:{color};padding:8px;border-radius:4px;">
            <b>Brightness:</b> {r.get('analysis', {}).get('brightness', 'N/A')} &nbsp;
            <b>Quality:</b> {quality} &nbsp;
            <b>Resolution:</b> {r.get('analysis', {}).get('resolution', 'N/A')}
          </div>
          {frame_tag}
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Scene Evaluation — {script['title']}</title>
<style>body{{font-family:Arial,sans-serif;margin:24px;background:#f5f5f5;}}</style>
</head>
<body>
<h1>Scene Evaluation Report</h1>
<p><b>Script:</b> {script['title']} &nbsp; <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
{rows}
</body></html>"""
    output_path.write_text(html)
    print(f"  HTML report saved: {output_path.name}")


# ─── Core Evaluation Logic ────────────────────────────────────────────────────

def run_evaluation(script_path: Path, output_dir: Path, mode: str) -> list[dict]:
    """Extract frames, analyze quality, return result list."""
    eval_dir = output_dir / "scene_evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)

    with open(script_path) as f:
        script = json.load(f)

    print(f"\n{'='*70}")
    print(f"  SCENE EVALUATION  [{mode.upper()} mode]")
    print(f"{'='*70}")
    print(f"  Script : {script['title']}")
    print(f"  Scenes : {len(script['scenes'])}\n")

    results = []

    for i, scene in enumerate(script["scenes"], start=1):
        video_path = find_scene_video(i, output_dir)
        frame_image = eval_dir / f"scene_{i}_frame.png"

        print(f"[Scene {i}] {scene['title'][:55]}")

        if not video_path:
            print(f"  No video found — skipping\n")
            continue

        print(f"  Video : {video_path.name}")

        if not extract_frame(video_path, FRAME_TIME, frame_image):
            print(f"  Frame extraction failed\n")
            continue

        analysis = analyze_image(frame_image)
        narration = scene.get("narration_text", "")
        word_count = len(narration.split())

        print(f"  Quality    : {analysis.get('quality', 'N/A')}  "
              f"(brightness {analysis.get('brightness', 'N/A')})")
        print(f"  Resolution : {analysis.get('resolution', 'N/A')}")
        print(f"  Narration  : {word_count} words")
        if narration.endswith("..."):
            print(f"  WARNING: Narration may be truncated")
        print()

        results.append({
            "scene": i,
            "title": scene["title"],
            "type": scene.get("scene_type", "unknown"),
            "frame_path": str(frame_image),
            "analysis": analysis,
            "quality": analysis.get("quality", "N/A"),
            "narration_words": word_count,
            "key_concepts": len(scene.get("key_concepts", [])),
        })

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    total = len(script["scenes"])
    done = len(results)
    good = sum(1 for r in results if r.get("quality") == "GOOD")
    avg_words = sum(r["narration_words"] for r in results) / done if done else 0

    print(f"  Frames extracted : {done}/{total}")
    print(f"  Good quality     : {good}/{done}")
    print(f"  Avg narration    : {avg_words:.0f} words/scene")
    print(f"  Output dir       : {eval_dir}/\n")

    # ── Full-mode extras ─────────────────────────────────────────────────────
    if mode == "full" and results:
        create_comparison_grid(results, eval_dir / "scene_comparison.png")
        create_html_report(script, results, eval_dir / "evaluation_report.html")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    json_path = eval_dir / "evaluation_results.json"
    with open(json_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "script_title": script["title"],
            "total_scenes": total,
            "frames_extracted": done,
            "results": results,
        }, f, indent=2)
    print(f"  Results JSON     : {json_path.name}")

    return results


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate rendered Manim scenes from the pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
modes:
  quick  Extract frames + brightness check (fast, no extra deps beyond Pillow)
  full   quick + comparison grid image + HTML report
""",
    )
    parser.add_argument(
        "--mode", choices=["quick", "full"], default="quick",
        help="Evaluation depth (default: quick)",
    )
    parser.add_argument(
        "--script", type=Path, default=SCRIPT_PATH,
        help="Path to script.json (default: output/script.json)",
    )
    parser.add_argument(
        "--output", type=Path, default=OUTPUT_DIR,
        help="Pipeline output directory (default: output/)",
    )
    args = parser.parse_args()

    if not args.script.exists():
        print(f"Error: script not found: {args.script}", file=sys.stderr)
        sys.exit(1)

    run_evaluation(args.script, args.output, args.mode)


if __name__ == "__main__":
    main()
