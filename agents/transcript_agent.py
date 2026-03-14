"""
DEPRECATED: agents.transcript_agent has been split into agents.transcript package.
This file is kept as a backward-compatibility shim.

Use instead:
    from agents.transcript import fetch_and_process_transcript, load_transcript_file
"""
import warnings
warnings.warn(
    "agents.transcript_agent is deprecated. Use agents.transcript instead.",
    DeprecationWarning,
    stacklevel=2,
)

from agents.transcript import (  # noqa: F401
    fetch_and_process_transcript,
    load_transcript_file,
    extract_video_id,
    fetch_transcript,
    summarize_transcript,
    extract_key_concepts,
    deep_process_transcript,
)
from agents.transcript.youtube_fetcher import group_transcript_by_minute  # noqa: F401
from agents.transcript.deep_analyzer import (  # noqa: F401
    process_transcript_chunks,
    extract_key_content_per_chunk,
    extract_narrative_structure,
)
from core.config import SCRIPT_MODEL as SUMMARIZER_MODEL  # noqa: F401

__all__ = [
    "fetch_and_process_transcript",
    "load_transcript_file",
    "extract_video_id",
    "fetch_transcript",
    "group_transcript_by_minute",
    "summarize_transcript",
    "extract_key_concepts",
    "deep_process_transcript",
    "process_transcript_chunks",
    "extract_key_content_per_chunk",
    "extract_narrative_structure",
    "SUMMARIZER_MODEL",
]
