"""
Agent 4: Video Assembly Agent
Combines per-scene Manim MP4 animations + TTS WAV narrations into a final video.
Uses MoviePy 2.x for assembly, subtitle overlay, and concatenation.

Fallback: If a scene has no MP4, generates a static title card using Pillow.
"""

import json
import os
import sys
import textwrap

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
    ColorClip,
    ImageClip,
)
from moviepy.video.fx import Resize


SUBTITLE_FONTSIZE = 18
SUBTITLE_COLOR = "white"
VIDEO_SIZE = (1280, 720)
FPS = 24

# Resolve a usable font path at import time
def _find_font() -> str:
    """Return path to a TTF/TTC font available on this system."""
    candidates = [
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        # Windows
        "C:/Windows/Fonts/arial.ttf",
    ]
    from PIL import ImageFont
    for path in candidates:
        import os
        if os.path.exists(path):
            try:
                ImageFont.truetype(path, 24)
                return path
            except Exception:
                continue
    raise RuntimeError("No usable system font found. Install DejaVu fonts or specify SUBTITLE_FONT.")

SUBTITLE_FONT = _find_font()


def make_title_card(title: str, narration_text: str, duration: float) -> CompositeVideoClip:
    """Create a simple black title card with text — fallback when no Manim MP4 exists."""
    bg = ColorClip(VIDEO_SIZE, color=(10, 10, 40)).with_duration(duration)

    title_clip = (
        TextClip(
            font=SUBTITLE_FONT,
            text=title,
            font_size=48,
            color="white",
            size=(VIDEO_SIZE[0] - 100, None),
            method="caption",
        )
        .with_position(("center", 200))
        .with_duration(duration)
    )

    wrapped = textwrap.fill(narration_text, width=70)
    body_clip = (
        TextClip(
            font=SUBTITLE_FONT,
            text=wrapped,
            font_size=28,
            color="#CCCCCC",
            size=(VIDEO_SIZE[0] - 100, None),
            method="caption",
        )
        .with_position(("center", 340))
        .with_duration(duration)
    )

    return CompositeVideoClip([bg, title_clip, body_clip], size=VIDEO_SIZE)


def add_subtitle_overlay(video_clip, narration_text: str) -> CompositeVideoClip:
    """Add bottom subtitle strip over existing video clip."""
    wrapped = textwrap.fill(narration_text, width=80)
    subtitle = (
        TextClip(
            font=SUBTITLE_FONT,
            text=wrapped,
            font_size=SUBTITLE_FONTSIZE,
            color=SUBTITLE_COLOR,
            size=(VIDEO_SIZE[0] - 40, None),
            method="caption",
            bg_color="black",
        )
        .with_position(("center", "bottom"))
        .with_duration(video_clip.duration)
    )
    return CompositeVideoClip([video_clip, subtitle], size=VIDEO_SIZE)


def assemble_scene(scene: dict, audio_path: str | None, mp4_path: str | None) -> CompositeVideoClip:
    """
    Combine animation + narration for one scene.
    Handles all missing-file combinations gracefully.
    """
    narration_text = scene["narration_text"]
    title = scene["title"]

    # Determine audio duration
    audio_clip = None
    audio_duration = 30.0  # default if no audio
    if audio_path and os.path.exists(audio_path):
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration

    # Load or create video
    if mp4_path and os.path.exists(mp4_path):
        video_clip = VideoFileClip(mp4_path).with_effects([Resize(VIDEO_SIZE)])
        # Match video duration to audio
        if video_clip.duration < audio_duration:
            # Freeze on a content frame (not the last frame which may be blank due to FadeOut)
            extra_duration = audio_duration - video_clip.duration

            # Find the best frame to freeze on (70% through video, before fade out)
            # Try multiple positions to find a non-blank frame
            best_frame = None
            for ratio in [0.7, 0.5, 0.8, 0.6, 0.9, 0.4]:
                frame_time = video_clip.duration * ratio
                candidate_frame = video_clip.get_frame(frame_time)
                # Check if frame has content (not mostly black)
                avg_brightness = candidate_frame.mean()
                if avg_brightness > 15:  # Not a blank/black frame
                    best_frame = candidate_frame
                    break

            # Fallback to 50% if all frames seem dark
            if best_frame is None:
                best_frame = video_clip.get_frame(video_clip.duration * 0.5)

            freeze_clip = (
                ImageClip(best_frame)
                .with_duration(extra_duration)
                .with_fps(video_clip.fps or FPS)
            )
            video_clip = concatenate_videoclips(
                [video_clip, freeze_clip], method="compose"
            )
        elif video_clip.duration > audio_duration:
            video_clip = video_clip.subclipped(0, audio_duration)
    else:
        print(f"    No MP4 for scene {scene['scene_id']}, using title card.")
        video_clip = make_title_card(title, narration_text, audio_duration)

    # Add subtitle overlay
    video_clip = add_subtitle_overlay(video_clip.with_duration(audio_duration), narration_text)

    # Attach audio
    if audio_clip:
        video_clip = video_clip.with_audio(audio_clip)

    return video_clip


def assemble_video(
    script_path: str,
    scene_results: list[dict],  # from animation_agent: [{...scene, mp4_path}]
    audio_results: list[dict],  # from tts_agent: [{...scene, audio_path}]
    output_path: str,
) -> str:
    """Assemble all scenes into the final video."""
    with open(script_path) as f:
        script = json.load(f)

    # Build lookup maps
    mp4_map = {r["scene_id"]: r.get("mp4_path") for r in scene_results}
    audio_map = {r["scene_id"]: r.get("audio_path") for r in audio_results}

    print(f"\n[Video Agent] Assembling {len(script['scenes'])} scenes...")

    clips = []
    for scene in script["scenes"]:
        sid = scene["scene_id"]
        mp4 = mp4_map.get(sid)
        audio = audio_map.get(sid)
        print(f"  Scene {sid}: {scene['title']}")
        print(f"    MP4: {mp4 or 'MISSING (using title card)'}")
        print(f"    Audio: {audio or 'MISSING (silent)'}")
        clip = assemble_scene(scene, audio, mp4)
        clips.append(clip)

    if not clips:
        raise RuntimeError("No scenes to assemble.")

    print(f"\n[Video Agent] Concatenating scenes...")
    final = concatenate_videoclips(clips, method="compose")

    # Add title screen at start
    title_card = make_title_card(
        script.get("title", "Educational Video"),
        "A YouTube AI Agent Framework for Indian Higher Education",
        4.0,
    )
    final = concatenate_videoclips([title_card, final], method="compose")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"[Video Agent] Writing final video → {output_path}")
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger="bar",
    )

    print(f"\n[Video Agent] Done! Final video: {output_path}")
    print(f"  Duration: {final.duration:.1f}s")
    return output_path


if __name__ == "__main__":
    # Standalone test mode: load results from JSON files
    if len(sys.argv) < 4:
        print("Usage: python video_agent.py script.json scene_results.json audio_results.json [output.mp4]")
        sys.exit(1)

    script = sys.argv[1]
    with open(sys.argv[2]) as f:
        scene_results = json.load(f)
    with open(sys.argv[3]) as f:
        audio_results = json.load(f)
    output = sys.argv[4] if len(sys.argv) > 4 else "output/final_video.mp4"

    assemble_video(script, scene_results, audio_results, output)
