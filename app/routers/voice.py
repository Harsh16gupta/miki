"""WebSocket voice endpoint (Phase 14).

Protocol (JSON frames are text, audio frames are binary):
- server -> {"type": "ready", "silence_threshold_seconds": N, ...}
- client -> {"type": "audio_format", "mime": "audio/webm"} once per turn,
  then ONE binary frame with the complete recorded Blob (one-shot transport;
  the server forwards the MIME to STT as Content-Type)
- client -> {"type": "end_of_turn"} to finalize now (browser VAD), or just
  stop sending: the server finalizes after silence_threshold_seconds
  with no frames (timing heuristic).
- server -> {"type": "answer", "transcript": ...}
- server -> {"type": "question", "text": ..., "finished": bool}
- server -> {"type": "audio", "format": "mp3", "data_b64": ...}
- server -> {"type": "done"} once the session reaches CLOSING.
- server -> {"type": "error", "detail": ...} on any failure; socket stays open.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session as DbSession

from app.auth.security import decode_access_token
from app.database import SessionLocal
from app.models import Session, User
from app.models.enums import SessionStatus
from app.policy import get_normal_policy
from app.voice import decide_turn_end, get_stt, get_tts
from app.voice.turns import MAX_BUFFER_BYTES

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice"])


async def _send_json(ws: WebSocket, payload: dict) -> None:
    await ws.send_text(json.dumps(payload))


def _user_from_ws_token(db: DbSession, token: str | None) -> User | None:
    """Decode an optional ``?token=`` query JWT; None when absent/invalid."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None
    return user


def _friendly_voice_error(e: Exception) -> str:
    """Map internal failures to speakable, non-leaky client messages."""
    msg = str(e)
    if "STT failed" in msg or "no speech" in msg or "Didn't catch" in msg:
        return "Didn't catch that clearly — tap Speak and try again."
    if "empty content" in msg or "Malformed LLM" in msg or "Invalid JSON" in msg:
        return "Miki's train of thought derailed — tap Speak and say that again."
    if "TTS" in msg or "no audio" in msg:
        return "Miki couldn't speak that reply — tap Speak to continue by voice."
    return msg[:300]


async def _finalize(
    ws: WebSocket,
    db: DbSession,
    session: Session,
    audio: bytes,
    content_type: str = "audio/webm",
    _retried: bool = False,
) -> bool:
    """Transcribe + engine + TTS + stream back. Returns finished flag.

    The engine is synchronous (blocking LLM HTTP); it runs in a worker
    thread so the event loop stays responsive. Audio goes out sentence by
    sentence so the client starts playing before synthesis finishes.
    One silent retry covers transient LLM glitches (the transcript is
    already in hand — no re-recording needed).
    """
    policy = get_normal_policy()
    try:
        stt, tts = get_stt(), get_tts()
        # Parallelize: kick off STT now; the blocking engine call runs in a
        # thread once the transcript lands.
        try:
            transcript = (await stt.transcribe(bytes(audio), content_type)).strip()
        except RuntimeError as e:
            # Raw provider bodies (e.g. Deepgram 400s) never reach the client.
            raise ValueError(f"STT failed: {e}") from e
        if not transcript:
            raise ValueError("STT returned no speech: try again")
        from app.interview import answer_session as _answer

        try:
            out = await asyncio.to_thread(
                _answer, db, session, policy, transcript
            )
        except ValueError as e:
            if not _retried and (
                "empty content" in str(e)
                or "Malformed LLM" in str(e)
                or "Invalid JSON" in str(e)
            ):
                logger.info("voice turn: transient LLM failure, retrying once")
                await asyncio.sleep(2)
                return await _finalize(
                    ws, db, session, audio, content_type, _retried=True
                )
            raise
        await _send_json(ws, {"type": "answer", "transcript": transcript})
        await _send_json(
            ws,
            {"type": "question", "text": out["question"], "finished": out["finished"]},
        )
        from app.voice.turns import synthesize_chunks

        chunks = await synthesize_chunks(tts.synthesize, out["question"])
        if not chunks:
            raise ValueError("TTS returned no audio: try again")
        for chunk in chunks:
            await _send_json(
                ws,
                {
                    "type": "audio",
                    "format": "mp3",
                    "data_b64": base64.b64encode(chunk).decode(),
                },
            )
    except Exception as e:
        logger.warning("voice turn failed: %s", e)
        await _send_json(ws, {"type": "error", "detail": _friendly_voice_error(e)})
        return False
    if out["finished"]:
        await _send_json(ws, {"type": "done"})
    return out["finished"]


@router.websocket("/session/{session_id}/voice")
async def voice_session(
    ws: WebSocket, session_id: int, token: str | None = None
) -> None:
    """Stream audio in, stream Miki's spoken reply out. Engine untouched.

    Browsers can't send ``Authorization`` headers over WebSocket, so an
    optional ``?token=<jwt>`` query param carries the owner credential.
    Owned sessions reject mismatched tokens; guest sessions stay open.
    """
    await ws.accept()
    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if session is None:
            await _send_json(ws, {"type": "error", "detail": "No such session"})
            await ws.close()
            return
        if session.user_id is not None:
            user = _user_from_ws_token(db, token)
            if user is None or user.id != session.user_id:
                await _send_json(ws, {"type": "error", "detail": "Not your session"})
                await ws.close()
                return
        policy = get_normal_policy()
        threshold = float(policy.silence_threshold_seconds)
        await _send_json(
            ws,
            {
                "type": "ready",
                "session_id": session_id,
                "silence_threshold_seconds": threshold,
            },
        )
        buffer = bytearray()
        audio_mime = "audio/webm"
        last_frame_at = time.monotonic()
        while True:
            if session.status != SessionStatus.IN_PROGRESS:
                await _send_json(ws, {"type": "done"})
                return
            try:
                message = await asyncio.wait_for(ws.receive(), timeout=threshold)
            except TimeoutError:
                if (
                    buffer
                    and len(buffer) >= 1000
                    and decide_turn_end(last_frame_at, time.monotonic(), threshold)
                ):
                    finished = await _finalize(ws, db, session, buffer, audio_mime)
                    buffer = bytearray()
                    db.refresh(session)
                    if finished:
                        return
                elif buffer and len(buffer) < 1000:
                    # Clear stray tiny noise chunks that would fail STT
                    buffer = bytearray()
                continue
            if message.get("bytes") is not None:
                chunk: bytes = message["bytes"]
                if len(buffer) + len(chunk) > MAX_BUFFER_BYTES:
                    await _send_json(
                        ws,
                        {"type": "error", "detail": "Audio too long, say less at once"},
                    )
                    buffer = bytearray()
                    continue
                buffer.extend(chunk)
                last_frame_at = time.monotonic()
            elif message.get("text") is not None:
                try:
                    control = json.loads(message["text"])
                except ValueError:
                    continue
                if control.get("type") == "audio_format":
                    mime = str(control.get("mime", "") or "")
                    if mime.startswith("audio/"):
                        audio_mime = mime.split(";")[0].strip() or audio_mime
                    continue
                if control.get("type") == "end_of_turn":
                    if not buffer or len(buffer) < 1000:
                        buffer = bytearray()
                        await _send_json(
                            ws,
                            {
                                "type": "error",
                                "detail": "Didn't catch that — tap Speak and try again.",
                            },
                        )
                        continue
                    finished = await _finalize(ws, db, session, buffer, audio_mime)
                    buffer = bytearray()
                    db.refresh(session)
                    if finished:
                        return
    except WebSocketDisconnect:
        logger.info("voice socket closed for session %d", session_id)
    except RuntimeError:
        # Starlette raises this on receive-after-disconnect races.
        logger.info("voice socket raced disconnect for session %d", session_id)
    finally:
        db.close()
