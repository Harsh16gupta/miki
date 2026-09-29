"""Turn handling for the voice layer (Phase 14).

Two pure pieces plus one integration seam, all engine-agnostic:
- :func:`decide_turn_end`: timing heuristic — the turn is over when no
  audio frame arrived for ``threshold_s`` (the policy's silence threshold).
- :func:`process_voice_turn`: STT buffer -> text -> unchanged
  :func:`answer_session` engine -> TTS reply audio. The engine code path is
  identical to the text loop; only the transport differs.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable

from sqlalchemy.orm import Session as DbSession

from app.interview import answer_session
from app.models import Session
from app.policy.loader import InterviewPolicy

SttFn = Callable[[bytes], Awaitable[str]]
TtsFn = Callable[[str], Awaitable[bytes]]

MAX_BUFFER_BYTES = 15 * 1024 * 1024


def decide_turn_end(last_frame_at: float, now: float, threshold_s: float) -> bool:
    """True when silence has lasted at least the threshold."""
    return (now - last_frame_at) >= threshold_s


_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
MAX_CHUNK_CHARS = 400


def split_sentences(text: str) -> list[str]:
    """Split reply text into TTS chunks (one sentence each, capped length).

    Short questions stay a single chunk; long ones split so the client can
    play audio progressively instead of waiting for one big synthesis.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return []
    chunks: list[str] = []
    for sentence in _SENTENCE_RE.split(cleaned):
        sentence = sentence.strip()
        if not sentence:
            continue
        while len(sentence) > MAX_CHUNK_CHARS:
            cut = sentence.rfind(",", 0, MAX_CHUNK_CHARS)
            cut = cut if cut > 100 else MAX_CHUNK_CHARS
            chunks.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if sentence:
            chunks.append(sentence)
    return chunks or [cleaned]


async def synthesize_chunks(tts: TtsFn, text: str) -> list[bytes]:
    """Synthesize each sentence chunk in parallel; order preserved."""
    chunks = split_sentences(text)
    audios = await asyncio.gather(*(tts(chunk) for chunk in chunks))
    return [a for a in audios if a]


async def process_voice_turn(
    db: DbSession,
    session: Session,
    policy: InterviewPolicy,
    audio: bytes,
    stt: SttFn,
    tts: TtsFn,
) -> dict:
    """Run one spoken turn end to end.

    Returns transcript/question/state/finished/claims plus ``audio`` (the
    full reply, first chunk — legacy single-frame clients) and
    ``audio_chunks`` (one mp3 per sentence, played in order).
    """
    if not audio:
        raise ValueError("Empty audio buffer: nothing to transcribe")
    if len(audio) > MAX_BUFFER_BYTES:
        raise ValueError("Audio buffer too long: send end_of_turn sooner")
    transcript = (await stt(audio)).strip()
    if not transcript:
        raise ValueError("STT returned no speech: try again")
    # answer_session is fully synchronous (blocking httpx). Callers inside
    # async WS handlers must run this in a worker thread (asyncio.to_thread).
    result = answer_session(db, session, policy, transcript)
    chunks = await synthesize_chunks(tts, result["question"])
    if not chunks:
        raise ValueError("TTS returned no audio: try again")
    return {
        "transcript": transcript,
        "question": result["question"],
        "state": result["state"],
        "finished": result["finished"],
        "claims_found": result["claims_found"],
        "audio": chunks[0],
        "audio_chunks": chunks,
    }
