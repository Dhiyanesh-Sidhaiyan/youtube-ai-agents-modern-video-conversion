"""
pipeline.py — Main entry point for the YouTube AI Agent Educational Video Generator

Orchestrates the 4-agent pipeline:
  Agent 1 (Script)     → abstract → script.json
  Agent 2 (Animation)  → script.json → scene MP4s
  Agent 3 (TTS)        → script.json → narration WAVs
  Agent 4 (Video)      → MP4s + WAVs → final_video.mp4

Usage:
  python pipeline.py [abstract_file] [language] [--skip-animation] [--skip-tts]

Examples:
  python pipeline.py abstracts.txt en
  python pipeline.py abstracts.txt hi
  python pipeline.py abstracts.txt en --skip-animation   # use existing scenes
  python pipeline.py abstracts.txt en --skip-tts         # silent video

Prerequisites:
  pip install crewai manim moviepy transformers torch accelerate scipy
  ollama serve
  ollama pull phi4
  ollama pull llama3
"""

import argparse
import json
import os
import shutil
import sys
import time

# Add project root to path so agents can be imported
sys.path.insert(0, os.path.dirname(__file__))

from agents.script_agent import generate_script
from agents.animation_agent import generate_all_scenes
from agents.tts_agent import generate_all_narrations
from agents.video_agent import assemble_video


# ── Paths ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR = "output"
SCRIPT_PATH = os.path.join(OUTPUT_DIR, "script.json")
SCENES_DIR = os.path.join(OUTPUT_DIR, "scenes")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
FINAL_VIDEO = os.path.join(OUTPUT_DIR, "final_video.mp4")
SCENE_RESULTS_PATH = os.path.join(OUTPUT_DIR, "scene_results.json")
AUDIO_RESULTS_PATH = os.path.join(OUTPUT_DIR, "audio_results.json")


def banner(text: str):
    width = 60
    print("\n" + "═" * width)
    print(f"  {text}")
    print("═" * width)


def cleanup_output(skip_script: bool, skip_animation: bool, skip_tts: bool):
    """Remove stale output files from previous runs to prevent contamination."""
    cleaned = False

    if not skip_animation:
        # Clean scene files, videos, and Manim caches
        for dirname in ["scenes", "videos", "texts", "images", "test", "debug_frames"]:
            path = os.path.join(OUTPUT_DIR, dirname)
            if os.path.exists(path):
                print(f"  Cleaning {path}/")
                shutil.rmtree(path)
                cleaned = True
        # Remove cached scene results
        if os.path.exists(SCENE_RESULTS_PATH):
            os.remove(SCENE_RESULTS_PATH)
            cleaned = True

    if not skip_tts:
        # Clean audio files
        if os.path.exists(AUDIO_DIR):
            print(f"  Cleaning {AUDIO_DIR}/")
            shutil.rmtree(AUDIO_DIR)
            cleaned = True
        if os.path.exists(AUDIO_RESULTS_PATH):
            os.remove(AUDIO_RESULTS_PATH)
            cleaned = True

    if not skip_script:
        # Clean script
        if os.path.exists(SCRIPT_PATH):
            os.remove(SCRIPT_PATH)
            cleaned = True

    if not cleaned:
        print("  Nothing to clean (using --skip flags)")


def parse_args():
    parser = argparse.ArgumentParser(description="Educational Video Generator Pipeline")
    parser.add_argument("abstract", nargs="?", default="abstracts.txt",
                        help="Path to abstract/paper text file (default: abstracts.txt)")
    parser.add_argument("language", nargs="?", default="en",
                        help="Narration language code: en, hi, ta, te, kn, ml, mr, bn, gu (default: en)")
    parser.add_argument("--skip-animation", action="store_true",
                        help="Skip animation generation, reuse existing scene MP4s")
    parser.add_argument("--skip-tts", action="store_true",
                        help="Skip TTS generation, produce silent video")
    parser.add_argument("--skip-script", action="store_true",
                        help="Skip script generation, reuse existing script.json")
    return parser.parse_args()


def check_ollama():
    """Verify Ollama is reachable before starting."""
    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"  Ollama connected. Available models: {', '.join(models) or 'none'}")
        if not any("phi4" in m or "phi-4" in m for m in models):
            print("  WARNING: phi4 not found. Run: ollama pull phi4")
        if not any("llama3" in m for m in models):
            print("  WARNING: llama3 not found. Run: ollama pull llama3")
    except Exception:
        print("  ERROR: Ollama is not running.")
        print("  Start it with:  ollama serve")
        print("  Then pull:      ollama pull phi4 && ollama pull llama3")
        sys.exit(1)


def run_pipeline(abstract_path: str, language: str,
                 skip_script: bool, skip_animation: bool, skip_tts: bool):
    start_time = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Pre-flight checks ────────────────────────────────────────────────────
    banner("Pre-flight Checks")
    if not os.path.exists(abstract_path):
        print(f"  ERROR: Abstract file not found: {abstract_path}")
        sys.exit(1)
    print(f"  Abstract: {abstract_path}")
    print(f"  Language: {language}")
    if not skip_animation:
        check_ollama()

    # ── Cleanup stale output ─────────────────────────────────────────────────
    banner("Cleaning Output")
    cleanup_output(skip_script, skip_animation, skip_tts)

    # Create output directories after cleanup
    os.makedirs(SCENES_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # ── Agent 1: Script ──────────────────────────────────────────────────────
    banner("Agent 1: Research & Script")
    if skip_script and os.path.exists(SCRIPT_PATH):
        print(f"  Skipping — reusing {SCRIPT_PATH}")
        with open(SCRIPT_PATH) as f:
            script = json.load(f)
        print(f"  Script: {script['title']} ({len(script['scenes'])} scenes)")
    else:
        script = generate_script(abstract_path, SCRIPT_PATH)

    # ── Agent 2: Animation ───────────────────────────────────────────────────
    banner("Agent 2: Animation Code")
    if skip_animation:
        if os.path.exists(SCENE_RESULTS_PATH):
            print(f"  Skipping — reusing {SCENE_RESULTS_PATH}")
            with open(SCENE_RESULTS_PATH) as f:
                scene_results = json.load(f)
        else:
            # No cached results — produce empty mp4_path entries so video agent uses title cards
            print("  Skipping animation (no cached results) — title cards will be used.")
            scene_results = [{**s, "mp4_path": None} for s in script["scenes"]]
    else:
        scene_results = generate_all_scenes(SCRIPT_PATH, SCENES_DIR)
        with open(SCENE_RESULTS_PATH, "w") as f:
            json.dump(scene_results, f, indent=2)

    # ── Agent 3: TTS ─────────────────────────────────────────────────────────
    banner("Agent 3: TTS Narration")
    if skip_tts:
        print("  Skipping TTS — video will be silent.")
        audio_results = [{**s, "audio_path": None} for s in script["scenes"]]
    elif os.path.exists(AUDIO_RESULTS_PATH):
        print(f"  Reusing {AUDIO_RESULTS_PATH}")
        with open(AUDIO_RESULTS_PATH) as f:
            audio_results = json.load(f)
    else:
        audio_results = generate_all_narrations(SCRIPT_PATH, AUDIO_DIR, language)
        with open(AUDIO_RESULTS_PATH, "w") as f:
            json.dump(audio_results, f, indent=2)

    # ── Agent 4: Video Assembly ───────────────────────────────────────────────
    banner("Agent 4: Video Assembly")
    output_path = assemble_video(SCRIPT_PATH, scene_results, audio_results, FINAL_VIDEO)

    # ── Summary ───────────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    banner("Pipeline Complete")
    print(f"  Output: {output_path}")
    print(f"  Time:   {elapsed/60:.1f} minutes")
    print(f"\n  Scenes rendered: {sum(1 for r in scene_results if r.get('mp4_path'))}/{len(scene_results)}")
    print(f"  Narrations:      {sum(1 for r in audio_results if r.get('audio_path'))}/{len(audio_results)}")


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        abstract_path=args.abstract,
        language=args.language,
        skip_script=args.skip_script,
        skip_animation=args.skip_animation,
        skip_tts=args.skip_tts,
    )
