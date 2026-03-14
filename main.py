#!/usr/bin/env python3
"""
main.py — Unified entry point for the YouTube AI Educational Video Generator

Handles both input modes in one command:
  - YouTube URL or local transcript file  → framework.py pipeline
  - Research abstract text file (.txt)    → pipeline.py pipeline

Usage:
    # YouTube / transcript mode
    python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
    python main.py transcript.log --language hi
    python main.py "https://youtu.be/VIDEO_ID" --output my_video.mp4

    # Abstract mode (research paper)
    python main.py abstracts.txt --language en
    python main.py abstracts.txt --skip-animation --skip-tts

    # Evaluate rendered scenes
    python main.py --evaluate
    python main.py --evaluate --eval-mode full

Prerequisites:
    ollama serve && ollama pull phi4 && ollama pull llama3
    pip install -r requirements.txt
"""

import argparse
import os
import sys
from datetime import datetime

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _is_abstract_file(path: str) -> bool:
    """Heuristic: treat local .txt files that are NOT transcript logs as abstract files."""
    if not os.path.isfile(path):
        return False
    if path.startswith("http://") or path.startswith("https://"):
        return False
    # transcript logs tend to be named transcript.log or transcript.json
    basename = os.path.basename(path).lower()
    if "transcript" in basename or basename.endswith(".log") or basename.endswith(".json"):
        return False
    return path.endswith(".txt")


def print_banner():
    print("\n" + "=" * 70)
    print("  AI Educational Video Generator")
    print("  YouTube Transcript  /  Research Abstract  →  Animated Video")
    print("=" * 70)


def run_youtube_mode(args):
    """Delegate to framework.py's run_pipeline."""
    from framework import run_pipeline

    output = args.output or f"output/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    run_pipeline(
        input_source=args.input,
        language=args.language,
        output_path=output,
        max_iterations=args.max_iterations,
        quality_threshold=args.quality_threshold,
    )


def run_abstract_mode(args):
    """Delegate to pipeline.py's entry logic (abstract → video)."""
    from agents.script_agent import generate_script
    from agents.animation_agent import generate_all_scenes
    from agents.tts_agent import generate_all_narrations
    from agents.video_agent import assemble_video
    from core.config import OUTPUT_DIR, SCENES_DIR, AUDIO_DIR

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    script_path = os.path.join(OUTPUT_DIR, "script.json")
    final_video = os.path.join(OUTPUT_DIR, "final_video.mp4")

    print(f"\n[Step 1/4] Generating script from abstract: {args.input}")
    script = generate_script(args.input, script_path)

    if not args.skip_animation:
        print(f"\n[Step 2/4] Generating animations...")
        generate_all_scenes(script_path, SCENES_DIR)
    else:
        print(f"\n[Step 2/4] Skipping animation (--skip-animation)")

    if not args.skip_tts:
        print(f"\n[Step 3/4] Generating TTS narration ({args.language})...")
        generate_all_narrations(script_path, AUDIO_DIR, language=args.language)
    else:
        print(f"\n[Step 3/4] Skipping TTS (--skip-tts)")

    print(f"\n[Step 4/4] Assembling final video...")
    assemble_video(script_path, SCENES_DIR, AUDIO_DIR, final_video)

    print(f"\nDone: {final_video}")


def run_evaluate_mode(args):
    """Run scene evaluation via evaluation/evaluate.py."""
    from pathlib import Path
    from evaluation.evaluate import run_evaluation

    script_path = Path(args.eval_script)
    output_dir = Path(args.eval_output)

    if not script_path.exists():
        print(f"Error: script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    run_evaluation(script_path, output_dir, args.eval_mode)


def main():
    parser = argparse.ArgumentParser(
        description="AI Educational Video Generator — unified entry point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # ── Positional (optional when --evaluate is used) ────────────────────────
    parser.add_argument(
        "input", nargs="?", default=None,
        help="YouTube URL, local transcript file, or research abstract .txt",
    )

    # ── Common flags ─────────────────────────────────────────────────────────
    parser.add_argument("--language", "-l", default="en",
                        choices=["en", "hi", "ta", "te", "kn", "ml", "mr", "bn", "gu", "pa"],
                        help="TTS narration language (default: en)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output video path (YouTube mode only)")

    # ── YouTube/framework flags ───────────────────────────────────────────────
    parser.add_argument("--max-iterations", type=int, default=3,
                        help="Max quality-refine iterations (default: 3)")
    parser.add_argument("--quality-threshold", type=float, default=80.0,
                        help="Minimum quality score (default: 80.0)")
    parser.add_argument("--script-only", action="store_true",
                        help="Stop after script generation (YouTube mode)")
    parser.add_argument("--transcript-only", action="store_true",
                        help="Stop after transcript fetch (YouTube mode)")

    # ── Abstract/pipeline flags ───────────────────────────────────────────────
    parser.add_argument("--skip-animation", action="store_true",
                        help="Skip animation step, reuse existing scenes (abstract mode)")
    parser.add_argument("--skip-tts", action="store_true",
                        help="Skip TTS step, produce silent video (abstract mode)")

    # ── Evaluate mode ─────────────────────────────────────────────────────────
    parser.add_argument("--evaluate", action="store_true",
                        help="Run scene evaluation instead of generation")
    parser.add_argument("--eval-mode", choices=["quick", "full"], default="quick",
                        help="Evaluation depth (default: quick)")
    parser.add_argument("--eval-script", default="output/script.json",
                        help="Script JSON for evaluation (default: output/script.json)")
    parser.add_argument("--eval-output", default="output",
                        help="Output dir for evaluation (default: output/)")

    args = parser.parse_args()

    print_banner()

    # ── Route to correct mode ─────────────────────────────────────────────────
    if args.evaluate:
        run_evaluate_mode(args)
        return

    if not args.input:
        parser.print_help()
        sys.exit(1)

    if _is_abstract_file(args.input):
        print(f"  Mode: Abstract → Video (research paper pipeline)")
        run_abstract_mode(args)
    else:
        print(f"  Mode: YouTube / Transcript → Video")
        run_youtube_mode(args)


if __name__ == "__main__":
    main()
