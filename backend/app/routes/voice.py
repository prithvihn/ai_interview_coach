"""
Voice routes — text-to-speech for the AI interviewer.
Converts text to natural-sounding audio using edge-tts neural voices.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import TTSRequest
from app.services.tts_service import text_to_speech, text_to_speech_stream, get_available_voices
import io

router = APIRouter()


@router.post("/tts")
async def speak(payload: TTSRequest):
    """
    Convert text to speech audio (MP3).
    Returns the full audio file as a streaming response.

    Usage: POST /api/tts with { "text": "...", "voice": "male_professional" }
    Response: audio/mpeg binary stream
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    if len(payload.text) > 2000:
        raise HTTPException(status_code=400, detail="Text too long (max 2000 chars)")

    try:
        audio_bytes = await text_to_speech(
            text=payload.text,
            voice=payload.voice,
            rate=payload.rate,
            pitch=payload.pitch,
        )

        if not audio_bytes:
            raise HTTPException(status_code=500, detail="TTS generation failed — empty audio")

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=reaction.mp3",
                "Content-Length": str(len(audio_bytes)),
                "Cache-Control": "public, max-age=3600",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.post("/tts/stream")
async def speak_stream(payload: TTSRequest):
    """
    Stream TTS audio in chunks for faster time-to-first-byte.
    Use this for longer texts where you want playback to start immediately.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    async def audio_stream():
        async for chunk in text_to_speech_stream(
            text=payload.text,
            voice=payload.voice,
            rate=payload.rate,
            pitch=payload.pitch,
        ):
            yield chunk

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=reaction.mp3"},
    )


@router.get("/tts/voices")
async def list_voices():
    """Return available voice presets."""
    return {"voices": get_available_voices()}
