# YouTube AI Agents - Educational Video Generator

Transform academic abstracts and papers into animated educational videos using a multi-agent AI pipeline.

## Overview

This project uses a 4-agent architecture powered by CrewAI and local LLMs (via Ollama) to automatically generate educational videos from text content:

| Agent | Role | Output |
|-------|------|--------|
| **Script Agent** | Converts abstract into structured script | `script.json` |
| **Animation Agent** | Generates Manim animation code | Scene MP4s |
| **TTS Agent** | Creates narration audio | WAV files |
| **Video Agent** | Assembles final video | `final_video.mp4` |

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

## Usage

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
├── pipeline.py              # Main orchestrator
├── agents/
│   ├── script_agent.py      # Abstract → structured script
│   ├── animation_agent.py   # Script → Manim animations
│   ├── prebuilt_scenes.py   # Reusable animation templates
│   ├── tts_agent.py         # Script → narration audio
│   └── video_agent.py       # Assembles final video
├── output/
│   ├── script.json          # Generated script
│   ├── scenes/              # Manim scene files
│   ├── audio/               # Narration WAV files
│   ├── videos/              # Individual scene videos
│   └── final_video.mp4      # Final output
├── abstracts.txt            # Sample input
└── requirements.txt
```

## Output

The pipeline generates:
- `output/script.json` - Structured script with scenes and narration
- `output/videos/` - Individual animated scene clips
- `output/audio/` - Narration audio files
- `output/final_video.mp4` - Complete assembled video

## Dependencies

- **CrewAI** - Multi-agent orchestration
- **Manim** - Mathematical animations
- **MoviePy** - Video editing and assembly
- **Transformers** - TTS models
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
