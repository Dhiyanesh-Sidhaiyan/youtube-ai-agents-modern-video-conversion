"""
Agent 3: TTS Narration Agent
Converts narration text to speech using Indic Parler TTS (AI4Bharat).
Falls back to Meta MMS for CPU-only environments.

Primary: huggingface.co/ai4bharat/indic-parler-tts  (21 Indian languages, Interspeech 2025)
Fallback: huggingface.co/facebook/mms-tts-hin       (CPU-friendly, 1107 languages)
"""

import json
import os
import sys

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
}

# Indic Parler TTS speaker descriptions per language
# See: huggingface.co/ai4bharat/indic-parler-tts model card
SPEAKER_DESCRIPTIONS = {
    "hi": "Ananya's voice is clear and expressive. The recording is of very high quality, very clear, with no background noise.",
    "en": "Arjun speaks in a clear, professional tone. The recording is of very high quality, with no background noise.",
    "ta": "Kavya's voice is natural and warm. The audio is clean with no background noise.",
    "te": "Ravi speaks clearly and steadily. The recording is of high quality with no noise.",
    "default": "The speaker has a clear voice. The recording is of high quality, with no background noise.",
}


def _load_indic_parler(language: str):
    """Load Indic Parler TTS model and tokenizer."""
    from transformers import AutoTokenizer, AutoModelForTextToSpeech
    import torch

    model_id = "ai4bharat/indic-parler-tts"
    print(f"  Loading Indic Parler TTS model (first run downloads ~2GB)...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForTextToSpeech.from_pretrained(model_id)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    return model, tokenizer, device


def _synthesize_indic_parler(text: str, language: str, output_path: str) -> bool:
    """Synthesize speech using Indic Parler TTS."""
    try:
        import torch
        import scipy.io.wavfile as wavfile

        model, tokenizer, device = _load_indic_parler(language)
        description = SPEAKER_DESCRIPTIONS.get(language, SPEAKER_DESCRIPTIONS["default"])

        # Tokenize description and input text
        desc_inputs = tokenizer(description, return_tensors="pt").to(device)
        text_inputs = tokenizer(text, return_tensors="pt").to(device)

        with torch.no_grad():
            generation = model.generate(
                input_ids=desc_inputs.input_ids,
                prompt_input_ids=text_inputs.input_ids,
                attention_mask=desc_inputs.attention_mask,
                prompt_attention_mask=text_inputs.attention_mask,
            )

        audio = generation.cpu().numpy().squeeze()
        sample_rate = model.config.sampling_rate
        wavfile.write(output_path, sample_rate, audio)
        return True
    except Exception as e:
        print(f"  Indic Parler TTS failed: {e}")
        return False


def _load_mms(language: str):
    """Load Meta MMS TTS model (CPU-friendly fallback)."""
    from transformers import VitsModel, AutoTokenizer

    # MMS uses language codes like 'hin' for Hindi
    lang_map = {
        "hi": "hin", "en": "eng", "ta": "tam", "te": "tel",
        "kn": "kan", "ml": "mal", "mr": "mar", "bn": "ben",
        "gu": "guj", "pa": "pan",
    }
    mms_lang = lang_map.get(language, "eng")
    model_id = f"facebook/mms-tts-{mms_lang}"
    print(f"  Loading Meta MMS model: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = VitsModel.from_pretrained(model_id)
    return model, tokenizer


def _synthesize_mms(text: str, language: str, output_path: str) -> bool:
    """Synthesize speech using Meta MMS (fallback)."""
    try:
        import torch
        import scipy.io.wavfile as wavfile

        model, tokenizer = _load_mms(language)
        inputs = tokenizer(text, return_tensors="pt")

        with torch.no_grad():
            output = model(**inputs).waveform

        audio = output.squeeze().cpu().numpy()
        wavfile.write(output_path, model.config.sampling_rate, audio)
        return True
    except Exception as e:
        print(f"  Meta MMS TTS failed: {e}")
        return False


def _synthesize_pyttsx3(text: str, output_path: str) -> bool:
    """Synthesize speech using pyttsx3 (offline, zero-download fallback)."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.setProperty("volume", 1.0)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        engine.stop()
        # pyttsx3 on macOS saves as AIFF; convert to WAV via wave/subprocess if needed
        if os.path.exists(output_path):
            return True
        # macOS may save .aiff next to the path — check
        aiff = output_path.replace(".wav", ".aiff")
        if os.path.exists(aiff):
            import subprocess
            subprocess.run(
                ["ffmpeg", "-y", "-i", aiff, output_path],
                capture_output=True,
            )
            return os.path.exists(output_path)
        return False
    except Exception as e:
        print(f"  pyttsx3 TTS failed: {e}")
        return False


def synthesize(text: str, language: str, output_path: str) -> bool:
    """
    Synthesize narration text to WAV file.
    Tries Indic Parler TTS → Meta MMS → pyttsx3 (offline).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"  Synthesizing ({SUPPORTED_LANGUAGES.get(language, language)}): {text[:60]}...")

    # Try primary: Indic Parler TTS
    if _synthesize_indic_parler(text, language, output_path):
        print(f"  Saved → {output_path} (Indic Parler TTS)")
        return True

    # Fallback 1: Meta MMS
    print(f"  Falling back to Meta MMS...")
    if _synthesize_mms(text, language, output_path):
        print(f"  Saved → {output_path} (Meta MMS)")
        return True

    # Fallback 2: pyttsx3 (offline, no download required)
    print(f"  Falling back to pyttsx3 (offline TTS)...")
    if _synthesize_pyttsx3(text, output_path):
        print(f"  Saved → {output_path} (pyttsx3)")
        return True

    print(f"  All TTS engines failed for scene.")
    return False


def generate_all_narrations(script_path: str, audio_dir: str, language: str = "en") -> list[dict]:
    """Generate narration audio for all scenes. Returns scene list with audio_path."""
    with open(script_path) as f:
        script = json.load(f)

    os.makedirs(audio_dir, exist_ok=True)
    results = []

    print(f"\n[TTS Agent] Generating narrations in {SUPPORTED_LANGUAGES.get(language, language)}...")

    for scene in script["scenes"]:
        scene_id = scene["scene_id"]
        audio_path = os.path.join(audio_dir, f"narration_{scene_id}.wav")

        print(f"\n  Scene {scene_id}: {scene['title']}")
        success = synthesize(scene["narration_text"], language, audio_path)
        results.append({
            **scene,
            "audio_path": audio_path if success else None,
        })

    successful = sum(1 for r in results if r["audio_path"])
    print(f"\n[TTS Agent] Done. {successful}/{len(results)} narrations generated.")
    return results


if __name__ == "__main__":
    script = sys.argv[1] if len(sys.argv) > 1 else "output/script.json"
    audio_dir = sys.argv[2] if len(sys.argv) > 2 else "output/audio"
    language = sys.argv[3] if len(sys.argv) > 3 else "en"
    generate_all_narrations(script, audio_dir, language)
