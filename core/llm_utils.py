"""
core/llm_utils.py — Shared utilities for processing LLM responses.

Consolidates extract_json() and extract_code() which were duplicated across
script_agent, transcript_agent, animation_agent, animation_fixer, and
dynamic_scene_generator.
"""

import json
import re


def extract_json(text: str) -> dict:
    """
    Extract JSON from an LLM response, handling common LLM output issues.

    Strips markdown fences, removes trailing commas, fixes control characters,
    and handles single-quote dicts that some models produce.
    """
    # Remove markdown code fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = re.sub(r"```", "", text).strip()

    # Find the outermost JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No valid JSON found in LLM response:\n{text[:500]}")

    json_str = match.group()

    # Fix common LLM JSON issues
    # 1. Remove trailing commas before } or ]
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
    # 2. Remove control characters that break JSON
    json_str = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", json_str)
    # 3. Fix unescaped newlines inside strings
    json_str = json_str.replace("\n", " ").replace("\r", " ")
    # 4. Remove // comments (common LLM mistake)
    json_str = re.sub(r"//.*?(?=[\n\r,}\]])", "", json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Try one more fix: some models use single quotes
        try:
            fixed = re.sub(r"'([^']*)':", r'"\1":', json_str)
            fixed = re.sub(r":\s*'([^']*)'", r': "\1"', fixed)
            return json.loads(fixed)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from LLM: {e}\n{json_str[:500]}")


def extract_code(text: str) -> str:
    """
    Extract Python code from an LLM response, stripping markdown fences.

    Handles both ```python ... ``` and plain code blocks.
    """
    text = re.sub(r"```(?:python)?\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()
