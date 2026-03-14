"""
core/ollama_client.py — Single Ollama LLM client for the entire pipeline.

Replaces 6 near-identical call_ollama() implementations scattered across:
  agents/script_agent.py, agents/transcript_agent.py, agents/animation_agent.py,
  agents/animation_fixer.py, agents/scene_templates.py, agents/dynamic_scene_generator.py

Usage:
    from core.ollama_client import call_ollama, check_ollama

    response = call_ollama(prompt, model="phi4", timeout=300)
    available_models = check_ollama()
"""

import requests
from core.config import (
    OLLAMA_URL,
    OLLAMA_TAGS_URL,
    FALLBACK_MODEL,
    TIMEOUT_MEDIUM,
)


def call_ollama(
    prompt: str,
    model: str = "phi4",
    timeout: int = TIMEOUT_MEDIUM,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    """
    Call Ollama to generate text.

    Automatically falls back to FALLBACK_MODEL on ReadTimeout.
    Raises RuntimeError with a helpful message on connection errors.

    Args:
        prompt:      The full prompt string.
        model:       Ollama model name (default: phi4).
        timeout:     Request timeout in seconds.
        temperature: Sampling temperature (lower = more deterministic).
        max_tokens:  Maximum tokens to generate.

    Returns:
        Generated text string.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json().get("response", "")

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama is not running.\n"
            "Start it with:  ollama serve\n"
            f"Then pull:      ollama pull {model}"
        )

    except requests.exceptions.ReadTimeout:
        if model != FALLBACK_MODEL:
            print(f"  {model} timed out after {timeout}s, retrying with {FALLBACK_MODEL}...")
            return call_ollama(
                prompt,
                model=FALLBACK_MODEL,
                timeout=timeout,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        raise RuntimeError(
            f"Ollama timed out after {timeout}s with {model}.\n"
            "The input may be too long. Try a shorter transcript or use --script-only."
        )


def check_ollama() -> list[str]:
    """
    Verify Ollama is reachable and return list of available model names.

    Raises RuntimeError if Ollama is not running.
    """
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        response.raise_for_status()
        models = [m["name"] for m in response.json().get("models", [])]
        return models
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama is not running.\n"
            "Start it with:  ollama serve\n"
            "Then pull:      ollama pull phi4 && ollama pull llama3"
        )
    except Exception as e:
        raise RuntimeError(f"Ollama health check failed: {e}")
