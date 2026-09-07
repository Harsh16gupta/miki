"""STT/TTS provider clients (Phase 14).

Thin httpx wrappers, no SDKs: Deepgram for speech-to-text, ElevenLabs for
text-to-speech. Keys come from the environment; when missing, factories
raise :class:`ProviderNotConfigured` with signup pointers instead of failing
cryptically mid-interview. Swap providers by replacing these two classes —
the WebSocket layer only depends on their method shapes.
"""

from __future__ import annotations

import os

import httpx


class ProviderNotConfigured(RuntimeError):
    """Raised when a voice provider key is missing."""


class DeepgramSTT:
    """Speech-to-text via Deepgram's prerecorded endpoint (one shot per turn)."""

    URL = "https://api.deepgram.com/v1/listen"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def transcribe(self, audio: bytes, content_type: str = "audio/webm") -> str:
        """Transcribe one audio buffer. Returns the transcript text."""
        params = {"model": "nova-2", "smart_format": "true"}
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": content_type,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.URL, params=params, headers=headers, content=audio
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"STT failed: HTTP {response.status_code}: {response.text[:300]}"
            )
        try:
            data = response.json()
            return data["results"]["channels"][0]["alternatives"][0]["transcript"]
        except (ValueError, KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"STT returned unexpected body: {e}") from e


class ElevenLabsTTS:
    """Text-to-speech via ElevenLabs. Returns MP3 bytes."""

    def __init__(self, api_key: str, voice_id: str) -> None:
        self.api_key = api_key
        self.voice_id = voice_id

    async def synthesize(self, text: str) -> bytes:
        """Synthesize one reply. Returns MP3 audio bytes."""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json={"text": text})
        if response.status_code >= 400:
            raise RuntimeError(
                f"TTS failed: HTTP {response.status_code}: {response.text[:300]}"
            )
        return response.content


def get_stt() -> DeepgramSTT:
    """Build the STT client from ``DEEPGRAM_API_KEY``."""
    key = os.getenv("DEEPGRAM_API_KEY")
    if not key:
        raise ProviderNotConfigured(
            "DEEPGRAM_API_KEY is not set. Sign up at "
            "https://console.deepgram.com, create a key, add it to .env."
        )
    return DeepgramSTT(key)


def get_tts() -> ElevenLabsTTS:
    """Build the TTS client from ``ELEVENLABS_API_KEY`` (+ voice id)."""
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise ProviderNotConfigured(
            "ELEVENLABS_API_KEY is not set. Sign up at "
            "https://elevenlabs.io, create a key, add it to .env."
        )
    voice = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    return ElevenLabsTTS(key, voice)
