# YouTube AI Agents - Educational Video Generator

Transform YouTube videos, academic abstracts, and papers into animated educational videos using a multi-agent AI pipeline.

## Demo

https://github.com/user-attachments/assets/final_video.mp4

<video src="output/final_video.mp4" controls width="100%"></video>

> Sample output generated from a YouTube transcript

## Overview

This project uses a 5-agent architecture powered by local LLMs (via Ollama) to automatically generate educational videos from YouTube URLs or text content:

| Agent | Role | Output |
|-------|------|--------|
| **Transcript Agent** | Fetches YouTube transcripts, extracts key concepts | `transcript_data.json` |
| **Script Agent** | Converts transcript/abstract into structured script | `script.json` |
| **Animation Agent** | Generates Manim animations using templates | Scene MP4s |
| **TTS Agent** | Creates narration audio (multi-language) | WAV files |
| **Video Agent** | Assembles final video with subtitles | `final_video.mp4` |

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) running locally
- FFmpeg (for video processing)

### Install Ollama Models

```bash
ollama serve
ollama pull phi4
ollama pull llama3
```

## Installation

```bash
# Clone the repository
git clone https://github.com/Dhiyanesh-Sidhaiyan/youtube-ai-agents-modern-video-conversion.git
cd youtube-ai-agents-modern-video-conversion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start (YouTube URL)

The easiest way to generate a video from a YouTube URL:

```bash
python framework.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Framework Options

```bash
# Generate video in Hindi
python framework.py "https://youtu.be/VIDEO_ID" --language hi

# Custom output path
python framework.py "https://youtube.com/watch?v=ID" --output my_video.mp4

# From local transcript file
python framework.py transcript.log --language en

# Only generate transcript (no video)
python framework.py "https://youtube.com/watch?v=ID" --transcript-only

# Only generate script (transcript + script agents)
python framework.py "https://youtube.com/watch?v=ID" --script-only
```

---

## Legacy Usage (Abstract-based)

For the original abstract-based pipeline:

```bash
python pipeline.py [abstract_file] [language] [options]
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `abstract_file` | `abstracts.txt` | Path to input text file |
| `language` | `en` | Narration language code |

### Supported Languages

`en` (English), `hi` (Hindi), `ta` (Tamil), `te` (Telugu), `kn` (Kannada), `ml` (Malayalam), `mr` (Marathi), `bn` (Bengali), `gu` (Gujarati)

### Options

| Flag | Description |
|------|-------------|
| `--skip-script` | Reuse existing `script.json` |
| `--skip-animation` | Reuse existing scene MP4s |
| `--skip-tts` | Generate silent video |

### Examples

```bash
# Generate video in English
python pipeline.py abstracts.txt en

# Generate video in Hindi
python pipeline.py abstracts.txt hi

# Regenerate only audio (keep existing animations)
python pipeline.py abstracts.txt en --skip-animation

# Quick test without TTS
python pipeline.py abstracts.txt en --skip-tts
```

## Project Structure

```
.
├── framework.py             # YouTube URL entry point (recommended)
├── pipeline.py              # Legacy abstract-based orchestrator
├── get_transcript.py        # Standalone transcript fetcher
├── agents/
│   ├── transcript_agent.py  # YouTube → preprocessed transcript
│   ├── script_agent.py      # Transcript/abstract → structured script
│   ├── scene_templates.py   # Parameterized Manim scene templates
│   ├── animation_agent.py   # Script → Manim animations
│   ├── prebuilt_scenes.py   # Legacy hardcoded animation templates
│   ├── tts_agent.py         # Script → narration audio
│   └── video_agent.py       # Assembles final video
├── output/
│   ├── transcript_data.json # Processed transcript with summary
│   ├── script.json          # Generated script with scene_type
│   ├── scenes/              # Manim scene files and MP4s
│   ├── audio/               # Narration WAV files
│   └── final_video.mp4      # Final output
├── abstracts.txt            # Sample abstract input
├── transcript.log           # Sample transcript input
└── requirements.txt
```

## Output

The pipeline generates:
- `output/transcript_data.json` - Processed transcript with summary and key concepts
- `output/script.json` - Structured script with scenes, narration, and scene types
- `output/scenes/` - Manim scene Python files and rendered MP4s
- `output/audio/` - Narration audio files (WAV)
- `output/final_video.mp4` - Complete assembled video with subtitles

## Dynamic Scene Templates

The framework uses parameterized Manim templates based on scene type:

| Scene Type | Use Case | Visual Style |
|------------|----------|--------------|
| `intro` | Opening scene | Title + bullet points |
| `concept` | Explain key ideas | Central box with details |
| `comparison` | Side-by-side analysis | Left vs Right columns |
| `process` | Step-by-step flow | Horizontal boxes with arrows |
| `example` | Code/demo showcase | Code box with result |
| `conclusion` | Summary/takeaways | Key points + final message |

The LLM automatically selects appropriate scene types based on content.

## Dependencies

- **Manim Community** - Mathematical animations
- **MoviePy 2.x** - Video editing and assembly
- **YouTube Transcript API** - Fetch YouTube transcripts
- **Ollama** - Local LLM inference (phi4, llama3)
- **Transformers** - TTS models (Indic Parler TTS, Meta MMS)
- **Torch** - ML backend

## Citation

If you use this project in your research or work, please cite it:

### BibTeX

```bibtex
@software{sidhaiyan2026youtube_ai_agents,
  author = {Sidhaiyan, Dhiyanesh},
  title = {YouTube AI Agents: Educational Video Generator},
  year = {2026},
  url = {https://github.com/Dhiyanesh-Sidhaiyan/youtube-ai-agents-modern-video-conversion}
}
```

### APA

Sidhaiyan, D. (2026). *YouTube AI Agents: Educational Video Generator* [Computer software]. https://github.com/Dhiyanesh-Sidhaiyan/youtube-ai-agents-modern-video-conversion

## License

MIT
