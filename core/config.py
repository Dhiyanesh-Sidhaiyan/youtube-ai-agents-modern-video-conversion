"""
core/config.py — Central configuration for the YouTube Transcript pipeline.

All constants previously scattered across 10+ agent files are consolidated here.
Change a value once; it takes effect everywhere.
"""

# ── Ollama / LLM ──────────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# Model roles
SCRIPT_MODEL = "phi4"          # Script generation (high quality, slower)
ANIMATION_MODEL = "phi4"       # Manim code generation
REVIEWER_MODEL = "llama3.2:3b" # Fast reviewer pass in Writer+Reviewer loop
FALLBACK_MODEL = "llama3"      # Fallback when primary model times out

# Timeouts (seconds)
TIMEOUT_SHORT = 45     # Quick calls (JSON parsing, small prompts)
TIMEOUT_MEDIUM = 120   # Standard generation
TIMEOUT_LONG = 300     # Manim code generation (phi4 14B on CPU)
TIMEOUT_SCRIPT = 600   # Script generation from long transcripts

# ── Quality & Retry ───────────────────────────────────────────────────────────

QUALITY_THRESHOLD = 80.0      # Min score (0–100) to accept a scene
MAX_RETRIES = 3               # LLM Writer+Reviewer loop max attempts
MAX_REFINE_ITERATIONS = 3     # Self-refine loop max attempts per scene
ENABLE_SELF_REFINE = True     # Toggle per-scene evaluation loop

# Scoring weights (visual + technical = 1.0)
VISUAL_WEIGHT = 0.6
TECHNICAL_WEIGHT = 0.4

# ── Paths ─────────────────────────────────────────────────────────────────────

OUTPUT_DIR = "output"
SCENES_DIR = "output/scenes"
AUDIO_DIR = "output/audio"
VIDEOS_DIR = "output/videos"

# Intermediate result files
SCRIPT_JSON = "output/script.json"
TRANSCRIPT_JSON = "output/transcript_data.json"
SCENE_RESULTS_JSON = "output/scene_results.json"
AUDIO_RESULTS_JSON = "output/audio_results.json"
EVALUATION_JSON = "output/evaluation.json"
VISUAL_ANALYSIS_JSON = "output/visual_analysis.json"

# ── Video ─────────────────────────────────────────────────────────────────────

VIDEO_SIZE = (1280, 720)
VIDEO_FPS = 24
MANIM_QUALITY = "ql"   # low quality flag for fast rendering during dev

SUBTITLE_FONTSIZE = 18

# ── TTS ───────────────────────────────────────────────────────────────────────

SUPPORTED_LANGUAGES = ["en", "hi", "ta", "te", "kn", "ml", "mr", "bn", "gu", "pa"]

# ── Manim Safe Area ───────────────────────────────────────────────────────────

SAFE_AREA = {
    "left": -6.0,
    "right": 6.0,
    "top": 3.5,
    "bottom": -3.5,
}

# ── Font Sizes ────────────────────────────────────────────────────────────────

FONT_SIZES = {
    "title": 44,
    "subtitle": 32,
    "heading": 30,
    "body": 26,
    "bullet": 24,
    "caption": 20,
}
