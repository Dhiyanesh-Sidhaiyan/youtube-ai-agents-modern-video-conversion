#!/usr/bin/env python3
"""
YouTube Transcript to Educational Video Framework

A dynamic framework that converts YouTube videos into animated educational videos
using a 4-agent pipeline:
  1. Transcript Agent - Fetches and preprocesses YouTube transcripts
  2. Script Agent - Generates scene-by-scene script with dynamic scene count
  3. Animation Agent - Creates Manim animations using parameterized templates
  4. TTS Agent - Generates narration audio
  5. Video Agent - Assembles final video

Usage:
    python framework.py <youtube_url>                  # Process YouTube URL
    python framework.py <transcript_file>              # Process local transcript
    python framework.py <youtube_url> --language hi    # Hindi narration
    python framework.py <youtube_url> --output out.mp4 # Custom output path

Examples:
    python framework.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    python framework.py transcript.log --language ta
    python framework.py "https://youtu.be/VIDEO_ID" --output my_video.mp4
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

# Ensure agents package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def generate_output_filename() -> str:
    """Generate timestamped output filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"output/video_{timestamp}.mp4"


def print_banner():
    """Print framework banner."""
    print("\n" + "=" * 70)
    print("  YouTube Transcript → Educational Video Framework")
    print("  6-Step Pipeline: Transcript → Script → Animation → TTS → Video → Eval")
    print("=" * 70)


def print_step(step_num: int, total: int, title: str):
    """Print step header."""
    print(f"\n{'─' * 70}")
    print(f"  Step {step_num}/{total}: {title}")
    print(f"{'─' * 70}")


def run_pipeline(
    input_source: str,
    language: str = "en",
    output_path: str = "output/final_video.mp4",
    max_iterations: int = 3,
    quality_threshold: float = 80.0,
) -> str:
    """
    Run the full YouTube-to-Video pipeline.

    Args:
        input_source: YouTube URL or path to transcript file
        language: Language code for narration (en, hi, ta, te, etc.)
        output_path: Path for final video output

    Returns:
        Path to the generated video file
    """
    start_time = time.time()
    output_dir = os.path.dirname(output_path) or "output"
    os.makedirs(output_dir, exist_ok=True)

    # Define intermediate file paths
    transcript_json = os.path.join(output_dir, "transcript_data.json")
    script_json = os.path.join(output_dir, "script.json")
    scenes_dir = os.path.join(output_dir, "scenes")
    audio_dir = os.path.join(output_dir, "audio")

    # ────────────────────────────────────────────────────────────────────────
    # Step 1: Fetch/Load Transcript
    # ────────────────────────────────────────────────────────────────────────
    print_step(1, 6, "Fetching/Loading Transcript")

    from agents.transcript_agent import (
        fetch_and_process_transcript,
        load_transcript_file,
    )

    if input_source.startswith("http"):
        # YouTube URL
        transcript_data = fetch_and_process_transcript(input_source, language)
    else:
        # Local file
        transcript_data = load_transcript_file(input_source)

    # Save transcript data for debugging/reuse
    with open(transcript_json, "w") as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)

    print(f"\n  Transcript saved: {transcript_json}")
    print(f"  Duration: {transcript_data.get('duration_minutes', 'N/A')} minutes")
    print(f"  Words: {transcript_data.get('word_count', 'N/A')}")

    # ────────────────────────────────────────────────────────────────────────
    # Step 2: Generate Script
    # ────────────────────────────────────────────────────────────────────────
    print_step(2, 6, "Generating Script")

    from agents.script_agent import generate_script_from_transcript

    script = generate_script_from_transcript(transcript_data, script_json)

    print(f"\n  Script saved: {script_json}")
    print(f"  Title: {script.get('title', 'Untitled')}")
    print(f"  Scenes: {len(script.get('scenes', []))}")

    # ────────────────────────────────────────────────────────────────────────
    # Step 3: Generate Animations
    # ────────────────────────────────────────────────────────────────────────
    print_step(3, 6, "Generating Manim Animations")

    from agents.animation_agent import generate_all_scenes

    scene_results = generate_all_scenes(script_json, scenes_dir)

    rendered = sum(1 for r in scene_results if r.get("mp4_path"))
    print(f"\n  Animations rendered: {rendered}/{len(scene_results)}")

    # ────────────────────────────────────────────────────────────────────────
    # Step 4: Generate Narrations
    # ────────────────────────────────────────────────────────────────────────
    print_step(4, 6, "Generating TTS Narrations")

    from agents.tts_agent import generate_all_narrations

    audio_results = generate_all_narrations(script_json, audio_dir, language)

    narrated = sum(1 for r in audio_results if r.get("audio_path"))
    print(f"\n  Narrations generated: {narrated}/{len(audio_results)}")

    # ────────────────────────────────────────────────────────────────────────
    # Step 5: Assemble Final Video
    # ────────────────────────────────────────────────────────────────────────
    print_step(5, 6, "Assembling Final Video")

    from agents.video_agent import assemble_video

    final_video = assemble_video(
        script_json,
        scene_results,
        audio_results,
        output_path,
    )

    # ────────────────────────────────────────────────────────────────────────
    # Step 6: Quality Evaluation & Visual Analysis
    # ────────────────────────────────────────────────────────────────────────
    print_step(6, 6, "Quality Evaluation & Visual Analysis")

    from agents.eval_agent import evaluate_pipeline
    from agents.visual_analyzer import analyze_all_scenes
    from agents.animation_fixer import fix_all_scenes

    eval_path = os.path.join(output_dir, "evaluation.json")
    visual_path = os.path.join(output_dir, "visual_analysis.json")

    # Initial evaluation
    evaluation = evaluate_pipeline(script_json, scene_results, audio_results, eval_path)

    # Visual frame-by-frame analysis
    visual_analysis = analyze_all_scenes(scene_results, visual_path)

    # Improvement loop - trigger on EITHER overall score OR visual quality
    iteration = 1
    visual_avg = visual_analysis.get("summary", {}).get("avg_quality", 100)
    needs_improvement = (
        evaluation.overall_score < quality_threshold or
        visual_avg < quality_threshold
    )

    while iteration < max_iterations and needs_improvement:
        needs_fix = visual_analysis.get("summary", {}).get("needs_improvement", [])

        if not needs_fix:
            # Check eval scores instead
            needs_fix = [
                e.scene_id for e in evaluation.scene_evaluations
                if e.overall_score < quality_threshold
            ]

        # Also check individual visual scores
        if not needs_fix:
            for scene_vis in visual_analysis.get("scenes", []):
                if scene_vis.get("quality_score", 100) < quality_threshold:
                    needs_fix.append(scene_vis["scene_id"])

        if not needs_fix:
            break

        print(f"\n  Improvement iteration {iteration + 1}/{max_iterations}")
        print(f"  Fixing {len(needs_fix)} scenes with visual/quality issues...")

        # Apply visual fixes using animation fixer
        scene_results = fix_all_scenes(scene_results, visual_analysis, scenes_dir)

        # Re-assemble video
        print(f"\n  Re-assembling video...")
        final_video = assemble_video(
            script_json,
            scene_results,
            audio_results,
            output_path,
        )

        # Re-evaluate
        evaluation = evaluate_pipeline(script_json, scene_results, audio_results, eval_path)
        visual_analysis = analyze_all_scenes(scene_results, visual_path)
        iteration += 1

        # Recalculate improvement condition
        visual_avg = visual_analysis.get("summary", {}).get("avg_quality", 100)
        needs_improvement = (
            evaluation.overall_score < quality_threshold or
            visual_avg < quality_threshold
        )

    if iteration > 1:
        print(f"\n  Improvement complete after {iteration} iterations")
        print(f"  Final score: {evaluation.overall_score:.1f}/100")

    # ────────────────────────────────────────────────────────────────────────
    # Summary
    # ────────────────────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("  Pipeline Complete!")
    print("=" * 70)
    print(f"  Input:         {input_source[:60]}...")
    print(f"  Language:      {language}")
    print(f"  Scenes:        {len(script.get('scenes', []))}")
    print(f"  Quality Score: {evaluation.overall_score:.1f}/100")
    print(f"  Iterations:    {iteration}")
    print(f"  Duration:      {elapsed:.1f} seconds")
    print(f"  Output:        {final_video}")
    print(f"  Eval Report:   {eval_path}")
    print(f"  Visual Report: {visual_path}")
    print("=" * 70 + "\n")

    return final_video


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Convert YouTube videos to animated educational videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python framework.py "https://www.youtube.com/watch?v=VIDEO_ID"
  python framework.py transcript.log --language hi
  python framework.py "https://youtu.be/VIDEO_ID" --output my_video.mp4
        """,
    )

    parser.add_argument(
        "input",
        help="YouTube URL or path to transcript file",
    )

    parser.add_argument(
        "--language", "-l",
        default="en",
        choices=["en", "hi", "ta", "te", "kn", "ml", "mr", "bn", "gu", "pa"],
        help="Language for TTS narration (default: en)",
    )

    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output video path (default: output/video_YYYYMMDD_HHMMSS.mp4)",
    )

    parser.add_argument(
        "--max-iterations", "-i",
        type=int,
        default=3,
        help="Max improvement iterations for low-quality scenes (default: 3)",
    )

    parser.add_argument(
        "--quality-threshold", "-q",
        type=float,
        default=80.0,
        help="Minimum quality score to accept (default: 80.0)",
    )

    parser.add_argument(
        "--transcript-only",
        action="store_true",
        help="Only fetch transcript, don't generate video",
    )

    parser.add_argument(
        "--script-only",
        action="store_true",
        help="Only generate script (transcript + script agents)",
    )

    args = parser.parse_args()

    print_banner()

    # Handle partial pipeline modes
    if args.transcript_only:
        from agents.transcript_agent import (
            fetch_and_process_transcript,
            load_transcript_file,
        )

        print_step(1, 1, "Fetching/Loading Transcript")

        if args.input.startswith("http"):
            result = fetch_and_process_transcript(args.input, args.language)
        else:
            result = load_transcript_file(args.input)

        output_json = "output/transcript_data.json"
        os.makedirs("output", exist_ok=True)
        with open(output_json, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n  Transcript saved: {output_json}")
        print(f"  Summary: {result.get('summary', '')[:200]}...")
        return

    if args.script_only:
        from agents.transcript_agent import (
            fetch_and_process_transcript,
            load_transcript_file,
        )
        from agents.script_agent import generate_script_from_transcript

        print_step(1, 2, "Fetching/Loading Transcript")

        if args.input.startswith("http"):
            transcript_data = fetch_and_process_transcript(args.input, args.language)
        else:
            transcript_data = load_transcript_file(args.input)

        print_step(2, 2, "Generating Script")
        script_json = "output/script.json"
        script = generate_script_from_transcript(transcript_data, script_json)

        print(f"\n  Script saved: {script_json}")
        print(f"  Scenes: {len(script.get('scenes', []))}")
        for s in script.get("scenes", []):
            print(f"    {s['scene_id']}. [{s.get('scene_type', 'N/A')}] {s['title']}")
        return

    # Full pipeline
    output_path = args.output or generate_output_filename()
    run_pipeline(
        input_source=args.input,
        language=args.language,
        output_path=output_path,
        max_iterations=args.max_iterations,
        quality_threshold=args.quality_threshold,
    )


if __name__ == "__main__":
    main()
