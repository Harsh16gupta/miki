"""Turn handling for the voice layer (Phase 14).

Two pure pieces plus one integration seam, all engine-agnostic:
- :func:`decide_turn_end`: timing heuristic — the turn is over when no
  audio frame arrived for ``threshold_s`` (the policy's silence threshold).
- :func:`process_voice_turn`: STT buffer -> text -> unchanged
  :func:`answer_session` engine -> TTS reply audio. The engine code path is
  identical to the text loop; only the transport differs.
"""

from __future__ import annotations

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


async def process_voice_turn(
    db: DbSession,
    session: Session,
    policy: InterviewPolicy,
    audio: bytes,
    stt: SttFn,
    tts: TtsFn,
) -> dict:
    """Run one spoken turn end to end. Returns transcript/question/audio."""
    if not audio:
        raise ValueError("Empty audio buffer: nothing to transcribe")
    if len(audio) > MAX_BUFFER_BYTES:
        raise ValueError("Audio buffer too long: send end_of_turn sooner")
    transcript = (await stt(audio)).strip()
    if not transcript:
        raise ValueError("STT returned no speech: try again")
    result = answer_session(db, session, policy, transcript)
    audio_out = await tts(result["question"])
    return {
        "transcript": transcript,
        "question": result["question"],
        "state": result["state"],
        "finished": result["finished"],
        "claims_found": result["claims_found"],
        "audio": audio_out,
    }
