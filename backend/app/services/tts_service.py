"""
Text-to-Speech service using edge-tts.
Converts interviewer reactions to natural-sounding audio.
Uses Microsoft Edge's neural TTS voices — free, no API key needed.
"""

import edge_tts
import io
import os
import hashlib
from app.config import settings


# ── Voice presets (natural-sounding neural voices) ────────────────────────────
VOICE_PRESETS = {
    # Male voices
    "male_professional": "en-US-GuyNeural",
    "male_casual": "en-US-DavisNeural",
    "male_british": "en-GB-RyanNeural",

    # Female voices
    "female_professional": "en-US-JennyNeural",
    "female_warm": "en-US-AriaNeural",
    "female_british": "en-GB-SoniaNeural",
}

DEFAULT_VOICE = "male_professional"  # Guy — deep, professional, HR-appropriate


async def text_to_speech(
    text: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> bytes:
    """
    Convert text to speech audio (MP3 bytes).

    Args:
        text: The text to speak
        voice: Voice preset key or direct edge-tts voice name
        rate: Speech rate adjustment (e.g., "+10%", "-5%")
        pitch: Pitch adjustment (e.g., "+2Hz", "-1Hz")

    Returns:
        MP3 audio bytes
    """
    # Resolve voice preset
    voice_name = VOICE_PRESETS.get(voice, voice)

    # Check cache first
    cache_key = _cache_key(text, voice_name, rate, pitch)
    cached = _get_cached(cache_key)
    if cached:
        return cached

    # Generate speech
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_name,
        rate=rate,
        pitch=pitch,
    )

    # Collect audio chunks into buffer
    audio_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])

    audio_bytes = audio_buffer.getvalue()

    # Cache the result
    _save_cached(cache_key, audio_bytes)

    return audio_bytes


async def text_to_speech_stream(
    text: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    pitch: str = "+0Hz",
):
    """
    Stream TTS audio chunks (async generator).
    Use this for large texts to start playback faster.
    """
    voice_name = VOICE_PRESETS.get(voice, voice)

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_name,
        rate=rate,
        pitch=pitch,
    )

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]


def get_available_voices() -> list[dict]:
    """Return the list of available voice presets."""
    return [
        {"key": key, "name": name, "gender": "male" if "male" in key else "female"}
        for key, name in VOICE_PRESETS.items()
    ]


# ── Cache helpers (avoid re-generating identical audio) ───────────────────────

_CACHE_DIR = os.path.join(settings.SESSIONS_DIR, "..", "tts_cache")


def _cache_key(text: str, voice: str, rate: str, pitch: str) -> str:
    raw = f"{text}|{voice}|{rate}|{pitch}"
    return hashlib.md5(raw.encode()).hexdigest()


def _get_cached(key: str) -> bytes | None:
    path = os.path.join(_CACHE_DIR, f"{key}.mp3")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None


def _save_cached(key: str, audio: bytes):
    os.makedirs(_CACHE_DIR, exist_ok=True)
    path = os.path.join(_CACHE_DIR, f"{key}.mp3")
    try:
        with open(path, "wb") as f:
            f.write(audio)
    except OSError:
        pass  # Cache write failure is non-critical
