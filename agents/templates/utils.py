"""
Utility functions for scene template parameter extraction.
Shared helpers for detecting generic content and extracting structured data from narration.
"""

import json
import re

from core.ollama_client import call_ollama
from core.config import TIMEOUT_SHORT

PARAM_EXTRACTOR_MODEL = "llama3"  # Faster model for param extraction
PARAM_EXTRACTOR_TIMEOUT = TIMEOUT_SHORT  # Increased timeout for better extraction
PARAM_EXTRACTOR_RETRY_TIMEOUT = 60  # Extended timeout for retries


# ─── Generic Content Detection & Fallback Helpers ───────────────────────────

def log_extraction_warning(scene_id: int, message: str):
    """Log warning about extraction issues for visibility."""
    print(f"  ⚠️  Scene {scene_id}: {message}")


def all_steps_generic(steps: list) -> bool:
    """
    Detect generic Step 1, Step 2, Step 3 patterns.
    Returns True if steps appear to be placeholder content.
    """
    if not steps:
        return True

    generic_patterns = [
        "Step 1", "Step 2", "Step 3", "Step 4", "Step 5",
        "First", "Second", "Third", "Fourth", "Fifth",
        "Point 1", "Point 2", "Point 3",
        "Feature A", "Feature B", "Feature C",
        "Item 1", "Item 2", "Item 3"
    ]

    generic_count = 0
    for step in steps:
        step_name = str(step[0]) if isinstance(step, (list, tuple)) and len(step) > 0 else str(step)
        step_desc = str(step[1]) if isinstance(step, (list, tuple)) and len(step) > 1 else ""

        # Check if step name matches generic patterns
        is_generic_name = any(g.lower() in step_name.lower() for g in generic_patterns)
        # Check if description is empty or too short
        is_empty_desc = len(step_desc.strip()) < 5

        if is_generic_name and is_empty_desc:
            generic_count += 1

    # If more than half are generic, consider it all generic
    return generic_count >= len(steps) / 2


def extract_steps_from_narration(narration: str, title: str = "") -> list:
    """
    Extract meaningful steps directly from narration text.
    Content-aware fallback when LLM extraction fails.
    """
    if not narration:
        return []

    steps = []

    # Try to find numbered patterns (1. xxx, 2. xxx)
    numbered_pattern = re.findall(r'(?:^|\. )(\d+)[.)\s]+([^.!?]+[.!?]?)', narration)
    if numbered_pattern and len(numbered_pattern) >= 2:
        for num, text in numbered_pattern[:5]:
            clean_text = text.strip()[:50]
            if len(clean_text) > 10:
                steps.append([f"Step {num}", clean_text])

    # Try "First..., Second..., Third..." patterns
    if not steps:
        ordinal_pattern = re.findall(
            r'\b(first|second|third|then|next|finally)[,\s]+([^.!?]+[.!?]?)',
            narration, re.IGNORECASE
        )
        ordinal_map = {"first": 1, "second": 2, "third": 3, "then": 4, "next": 5, "finally": 6}
        for ordinal, text in ordinal_pattern[:5]:
            clean_text = text.strip()[:50]
            if len(clean_text) > 10:
                idx = ordinal_map.get(ordinal.lower(), len(steps) + 1)
                steps.append([f"Step {idx}", clean_text])

    # Fallback: Split narration into key sentences
    if not steps:
        sentences = re.split(r'[.!?]+', narration)
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:4]

        for i, sentence in enumerate(meaningful_sentences, 1):
            # Extract first 3-4 words as step name
            words = sentence.split()[:4]
            step_name = ' '.join(words)[:15]
            step_desc = sentence[:50]
            steps.append([step_name, step_desc])

    # If still nothing, use title as single step
    if not steps and title:
        steps = [[title[:15], narration[:50] if narration else "Key concept"]]

    return steps if steps else [["Overview", "See visual demonstration"]]


def extract_bullet_points_from_narration(narration: str, count: int = 3) -> list:
    """
    Extract meaningful bullet points directly from narration.
    Used as fallback when LLM extraction fails.
    """
    if not narration:
        return ["See visual demonstration"]

    # Split into sentences
    sentences = re.split(r'[.!?]+', narration)
    meaningful = [s.strip() for s in sentences if len(s.strip()) > 15]

    # Take the most meaningful sentences (not too long, not too short)
    scored = []
    for s in meaningful:
        # Prefer medium-length sentences with keywords
        score = 0
        if 20 < len(s) < 80:
            score += 2
        if any(kw in s.lower() for kw in ['important', 'key', 'note', 'remember', 'main', 'first', 'second']):
            score += 1
        scored.append((score, s))

    scored.sort(reverse=True, key=lambda x: x[0])
    points = [s[:50] for _, s in scored[:count]]

    # Ensure we have enough points
    while len(points) < count and meaningful:
        for s in meaningful:
            if s[:50] not in points:
                points.append(s[:50])
                if len(points) >= count:
                    break

    return points if points else [narration[:50]]


def all_points_generic(points: list) -> bool:
    """Check if bullet points are generic placeholders."""
    if not points:
        return True

    generic_patterns = [
        "point 1", "point 2", "point 3",
        "key point 1", "key point 2",
        "feature a", "feature b",
        "item 1", "item 2"
    ]

    generic_count = sum(
        1 for p in points
        if any(g in str(p).lower() for g in generic_patterns)
    )
    return generic_count >= len(points) / 2


def call_ollama_json(prompt: str, timeout: int = None, retry_on_fail: bool = False) -> dict:
    """
    Call Ollama and parse JSON response.

    Args:
        prompt: The prompt to send
        timeout: Custom timeout in seconds (default: PARAM_EXTRACTOR_TIMEOUT)
        retry_on_fail: If True, retry with extended timeout on failure

    Returns:
        Parsed JSON dict, or empty dict on failure
    """
    timeout = timeout or PARAM_EXTRACTOR_TIMEOUT

    def _make_request(current_timeout: int) -> dict:
        try:
            text = call_ollama(prompt, model=PARAM_EXTRACTOR_MODEL, timeout=current_timeout, temperature=0.2)
            # Extract JSON from response
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                json_str = match.group()
                # Fix common JSON issues
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)  # trailing commas
                json_str = json_str.replace("\n", " ")  # newlines
                return json.loads(json_str)
        except TimeoutError:
            print(f"  ⏱️  Param extraction timed out ({current_timeout}s)")
            return None
        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"  ⚠️  Param extraction error: {e}")
            return None
        return {}

    # First attempt
    result = _make_request(timeout)

    # Retry with extended timeout if enabled and first attempt failed
    if result is None and retry_on_fail:
        print(f"  🔄 Retrying with extended timeout ({PARAM_EXTRACTOR_RETRY_TIMEOUT}s)...")
        result = _make_request(PARAM_EXTRACTOR_RETRY_TIMEOUT)

    return result if result is not None else {}
