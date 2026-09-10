"""WebSocket voice endpoint (Phase 14).

Protocol (JSON frames are text, audio frames are binary):
- server -> {"type": "ready", "silence_threshold_seconds": N, ...}
- client -> binary audio frames while speaking
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
from app.voice import decide_turn_end, get_stt, get_tts, process_voice_turn
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


async def _finalize(
    ws: WebSocket, db: DbSession, session: Session, audio: bytes
) -> bool:
    """Transcribe + engine + TTS + stream back. Returns finished flag."""
    policy = get_normal_policy()
    try:
        stt, tts = get_stt(), get_tts()
        out = await process_voice_turn(
            db,
            session,
            policy,
            bytes(audio),
            stt.transcribe,
            tts.synthesize,
        )
    except Exception as e:
        logger.warning("voice turn failed: %s", e)
        await _send_json(ws, {"type": "error", "detail": str(e)[:300]})
        return False
    await _send_json(ws, {"type": "answer", "transcript": out["transcript"]})
    await _send_json(
        ws,
        {"type": "question", "text": out["question"], "finished": out["finished"]},
    )
    await _send_json(
        ws,
        {
            "type": "audio",
            "format": "mp3",
            "data_b64": base64.b64encode(out["audio"]).decode(),
        },
    )
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
                    finished = await _finalize(ws, db, session, buffer)
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
                if control.get("type") == "end_of_turn" and buffer:
                    finished = await _finalize(ws, db, session, buffer)
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
