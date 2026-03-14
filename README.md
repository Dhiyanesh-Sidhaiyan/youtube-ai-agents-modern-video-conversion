# YouTube AI Agents — Educational Video Generator

Transform YouTube videos, research paper abstracts, and academic transcripts into animated educational videos using a local, fully offline multi-agent AI pipeline.

---

## Demo Videos

### Demo 1 — Research Paper to Animated Video
[![Demo 1](https://img.youtube.com/vi/0Izb0nODvtI/maxresdefault.jpg)](https://youtu.be/0Izb0nODvtI)

### Demo 2 — YouTube Transcript to Educational Video
[![Demo 2](https://img.youtube.com/vi/FFkHsyre4PU/maxresdefault.jpg)](https://youtu.be/FFkHsyre4PU)

> Click the thumbnails to watch on YouTube.

---

## Overview

This project uses a **5-agent architecture** powered by local LLMs (via Ollama) to automatically generate animated educational videos from YouTube URLs, transcripts, or research paper abstracts. The pipeline runs entirely offline — no OpenAI API keys, no cloud services.

```
YouTube URL / Abstract
        │
        ▼
  [Transcript Agent]  ──→  transcript_data.json
        │
        ▼
  [Script Agent]      ──→  script.json  (19 scene types)
        │
        ▼
  [Animation Agent]   ──→  output/scenes/scene_N.mp4
  (Writer + Reviewer          (Manim CE, retry loop)
   Self-Refine loop)
        │
        ▼
  [TTS Agent]         ──→  output/audio/narration_N.wav
  (Indic Parler TTS           (10 Indian languages)
   + MMS fallback)
        │
        ▼
  [Video Agent]       ──→  output/final_video.mp4
```

---

## Agent Roles

| Agent | Role | Output |
|---|---|---|
| **Transcript Agent** | Fetches YouTube transcripts, deep content extraction (NotebookLM-style) | `transcript_data.json` |
| **Script Agent** | Converts transcript/abstract into a structured multi-scene script | `script.json` |
| **Animation Agent** | Generates Manim CE animations via Writer+Reviewer loop (up to 3 retries) | Scene MP4s |
| **TTS Agent** | Narration audio in 10 Indian languages | WAV files |
| **Video Agent** | Assembles scenes + audio into the final video | `final_video.mp4` |

---

## Features

- **Fully local and offline** — Ollama + phi4 + llama3, no API keys needed
- **19 parameterized scene templates** — intro, concept, comparison, process, math formula, equation derivation, geometric theorem, matrix operations, data charts, timelines, decision trees, and more
- **Writer + Reviewer retry loop** — animation code is reviewed and fixed automatically (up to 3 retries)
- **Self-Refine loop** — Generate → Evaluate → Feedback → Refine (up to 3 iterations, quality threshold 80/100)
- **10 Indian languages** for narration via Indic Parler TTS
- **Graceful degradation** — title card fallback if Manim render fails, silent video if TTS fails
- **Resumable pipeline** — intermediate JSON results allow skipping completed stages
- **Quality evaluation** — automated scene scoring (60% visual + 40% technical)

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) running locally
- FFmpeg (for video processing)

### Pull Ollama Models

```bash
ollama serve
ollama pull phi4        # Script + Animation (14B)
ollama pull llama3      # Fallback
ollama pull llama3.2:3b # Reviewer (lightweight)
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/Dhiyanesh-Sidhaiyan/youtube-ai-agents-modern-video-conversion.git
cd youtube-ai-agents-modern-video-conversion

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

All modes go through the unified entry point `main.py`.

### YouTube URL

```bash
python3 main.py "https://www.youtube.com/watch?v=VIDEO_ID"
python3 main.py "https://youtu.be/VIDEO_ID" --language hi
```

### Local Transcript File

```bash
python3 main.py transcript.log --language ta
```

### Research Paper Abstract

```bash
python3 main.py abstracts.txt --language en
python3 main.py abstracts.txt --skip-animation --skip-tts  # script only
```

### Evaluate Rendered Scenes

```bash
python3 main.py --evaluate
python3 main.py --evaluate --eval-mode full
python3 evaluation/evaluate.py --mode full
```

### All CLI Options

| Flag | Default | Description |
|---|---|---|
| `--language` | `en` | Narration language code |
| `--output` | `output/final_video.mp4` | Output video path |
| `--max-iterations` | `3` | Max Self-Refine iterations |
| `--quality-threshold` | `80` | Min quality score (0–100) |
| `--skip-animation` | off | Reuse existing scene MP4s |
| `--skip-tts` | off | Generate silent video |
| `--evaluate` | off | Run scene quality evaluation |
| `--eval-mode` | `quick` | `quick` or `full` (HTML report) |

---

## Supported Languages

| Code | Language | TTS Engine |
|---|---|---|
| `en` | English | Indic Parler TTS |
| `hi` | Hindi | Indic Parler TTS |
| `ta` | Tamil | Indic Parler TTS |
| `te` | Telugu | Indic Parler TTS |
| `kn` | Kannada | Indic Parler TTS |
| `ml` | Malayalam | Indic Parler TTS |
| `mr` | Marathi | Indic Parler TTS |
| `bn` | Bengali | Indic Parler TTS |
| `gu` | Gujarati | Indic Parler TTS |
| `pa` | Punjabi | Indic Parler TTS |

Fallback: `facebook/mms-tts` (CPU-friendly) when Indic Parler TTS is unavailable.

---

## Scene Templates

The pipeline selects from 19 parameterized Manim scene types based on content:

| Category | Templates |
|---|---|
| **Narrative** | `intro`, `concept`, `comparison`, `process`, `example`, `conclusion` |
| **Math** | `math_formula`, `equation_derivation`, `geometric_theorem`, `matrix_operation` |
| **Data** | `data_chart`, `graph_visualization`, `metrics` |
| **Structure** | `timeline`, `diagram`, `hierarchy`, `decision_tree` |
| **Visual** | `visual_explanation`, `info_card` |

---

## Project Structure

```
youtube_transcript/
├── main.py                    # Unified entry point (all modes)
├── pipeline.py                # Legacy abstract pipeline (deprecated)
├── framework.py               # Legacy YouTube pipeline (deprecated)
├── get_transcript.py          # Standalone transcript fetcher
├── abstracts.txt              # Sample abstract input
├── requirements.txt
│
├── core/                      # Shared infrastructure
│   ├── config.py              # All constants (models, timeouts, thresholds)
│   ├── ollama_client.py       # Single call_ollama() used by all agents
│   └── llm_utils.py           # extract_json(), extract_code()
│
├── prompts/                   # All LLM prompt strings
│   ├── script_prompts.py
│   ├── animation_prompts.py
│   └── scene_gen_prompts.py
│
├── agents/                    # Agent business logic
│   ├── script_agent.py        # Abstract/transcript → structured JSON script
│   ├── animation_agent.py     # Script → Manim code → MP4 (Writer+Reviewer)
│   ├── animation_fixer.py     # Manim error detection + fix generation
│   ├── tts_agent.py           # Script → narration WAV
│   ├── video_agent.py         # Scene MP4s + audio → final_video.mp4
│   ├── transcript_agent.py    # YouTube → preprocessed transcript
│   ├── dynamic_scene_generator.py  # Template parameter extraction + rendering
│   ├── scene_templates.py     # 19 parameterized Manim templates
│   ├── scene_evaluator.py     # Per-scene quality scorer
│   ├── visual_analyzer.py     # Frame-level visual analysis
│   ├── code_validator.py      # Manim code syntax validation
│   ├── eval_agent.py          # Scene evaluation agent
│   ├── layout_system.py       # Manim layout helpers
│   ├── layout_validator.py    # Layout constraint validation
│   ├── prebuilt_scenes.py     # Legacy hardcoded templates
│   ├── scene_wrapper.py       # Scene execution wrapper
│   │
│   ├── transcript/            # Transcript sub-package
│   │   ├── youtube_fetcher.py
│   │   ├── transcript_processor.py
│   │   └── deep_analyzer.py   # NotebookLM-style chunk extraction
│   │
│   ├── templates/             # Template registry + 19 template strings
│   │   ├── registry.py
│   │   ├── utils.py
│   │   ├── template_strings/  # One file per template type
│   │   └── param_extractors/  # One extractor per template type
│   │
│   ├── rendering/
│   │   └── manim_renderer.py  # Manim subprocess renderer
│   │
│   ├── evaluation/            # Agent-level evaluation
│   │   ├── scene_quality.py
│   │   ├── self_refine.py     # Self-Refine loop (Generate→Eval→Fix)
│   │   └── content_variety.py
│   │
│   └── visual_analysis/       # Post-render visual checks
│       ├── frame_extractor.py
│       ├── frame_analyzer.py
│       └── fix_generator.py
│
├── evaluation/                # Standalone evaluation CLI
│   └── evaluate.py            # --mode quick|full, JSON + HTML reports
│
└── output/
    ├── transcript_data.json
    ├── script.json
    ├── scenes/                # Manim .py files + rendered MP4s
    ├── audio/                 # Narration WAV files
    ├── final_video.mp4
    └── scene_evaluation/      # Quality evaluation results
        └── evaluation_results.json
```

---

## Configuration

Key values from `core/config.py`:

| Setting | Value | Description |
|---|---|---|
| `SCRIPT_MODEL` | `phi4` | LLM for script generation |
| `ANIMATION_MODEL` | `phi4` | LLM for Manim code generation |
| `REVIEWER_MODEL` | `llama3.2:3b` | Lightweight reviewer LLM |
| `FALLBACK_MODEL` | `llama3` | Fallback LLM |
| `TIMEOUT_SHORT` | 45s | Fast operations |
| `TIMEOUT_MEDIUM` | 120s | Standard LLM calls |
| `TIMEOUT_LONG` | 300s | Complex generation |
| `TIMEOUT_SCRIPT` | 600s | Full script generation |
| `QUALITY_THRESHOLD` | 80.0 | Minimum scene quality score |
| `MAX_REFINE_ITERATIONS` | 3 | Self-Refine loop limit |
| `VISUAL_WEIGHT` | 0.6 | Visual score weight |
| `TECHNICAL_WEIGHT` | 0.4 | Technical score weight |
| `VIDEO_WIDTH` | 1280 | Output video width |
| `VIDEO_HEIGHT` | 720 | Output video height |
| `VIDEO_FPS` | 24 | Output frame rate |

---

## Technology Stack

| Component | Technology |
|---|---|
| LLM inference | Ollama + Phi-4 (14B), Llama 3, Llama 3.2:3b |
| Animation | Manim Community Edition |
| TTS (primary) | `ai4bharat/indic-parler-tts` |
| TTS (fallback) | `facebook/mms-tts` |
| Video assembly | MoviePy 2.x |
| Transcript fetch | `youtube-transcript-api` |

---

## Dependencies

```
manim>=0.18.0
moviepy>=2.0.0
transformers>=4.40.0
torch>=2.2.0
accelerate>=0.27.0
Pillow>=10.0.0
requests>=2.32.0
pyttsx3>=2.90
scipy>=1.11.0
youtube-transcript-api>=0.6.0
numpy>=1.24.0
pyspellchecker>=0.8.0
```

---

## Citation

If you use this project in your research, please cite:

```bibtex
@software{sidhaiyan2026youtube_ai_agents,
  author = {Sidhaiyan, Dhiyanesh},
  title  = {YouTube AI Agents: Educational Video Generator},
  year   = {2026},
  url    = {https://github.com/Dhiyanesh-Sidhaiyan/youtube-ai-agents-modern-video-conversion}
}
```

---

## License

MIT
