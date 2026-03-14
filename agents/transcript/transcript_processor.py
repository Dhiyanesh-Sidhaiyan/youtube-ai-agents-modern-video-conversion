"""
Basic transcript processing: LLM summarization and concept extraction.

Responsibility: LLM calls for basic understanding of transcript content.
No YouTube API, no deep chunking, no file I/O.
"""

import json
import re

from core.ollama_client import call_ollama
from core.config import SCRIPT_MODEL, TIMEOUT_MEDIUM

SUMMARIZER_MODEL = SCRIPT_MODEL


def summarize_transcript(full_text: str) -> str:
    """Use LLM to create a concise summary of the transcript."""
    prompt = f"""Summarize the following YouTube video transcript into a concise abstract (150-250 words).
Focus on:
1. The main topic and purpose
2. Key concepts and ideas presented
3. Important examples or demonstrations
4. Conclusions or takeaways

TRANSCRIPT:
{full_text[:8000]}  # Limit to avoid token overflow

SUMMARY (150-250 words):"""

    try:
        summary = call_ollama(prompt, model=SUMMARIZER_MODEL, timeout=TIMEOUT_MEDIUM)
        return summary if summary else full_text[:500]
    except Exception as e:
        print(f"  Ollama error during summarization: {e}")
        return full_text[:500]  # Fallback to truncated text


def extract_key_concepts(full_text: str) -> list:
    """Use LLM to extract key concepts from the transcript."""
    prompt = f"""Extract 5-8 key concepts or topics from this YouTube video transcript.
Return ONLY a JSON array of strings, no explanation.

TRANSCRIPT:
{full_text[:6000]}

KEY CONCEPTS (JSON array):"""

    try:
        response = call_ollama(prompt, model=SUMMARIZER_MODEL, timeout=TIMEOUT_MEDIUM)
    except Exception as e:
        print(f"  Ollama error during concept extraction: {e}")
        response = ""

    # Try to parse JSON array
    try:
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            concepts = json.loads(match.group())
            return concepts[:8]  # Limit to 8
    except json.JSONDecodeError:
        pass

    # Fallback: extract quoted strings
    concepts = re.findall(r'"([^"]+)"', response)
    if concepts:
        return concepts[:8]

    # Last resort: return generic concepts
    return ["Main Topic", "Key Idea", "Example", "Conclusion"]
