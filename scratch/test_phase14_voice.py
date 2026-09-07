"""Phase 14 checkpoint: voice adapter without providers or mic (real LLM).

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase14_voice.py``.
- decide_turn_end: pure timing checks, no IO.
- Provider factories raise helpfully with keys missing.
- process_voice_turn with fake STT/TTS + one real answer_session cycle.
- Full WS round trip with monkeypatched providers (fake STT/TTS).
Cleans up afterwards.
"""

import asyncio
import json
import os

from fastapi.testclient import TestClient

import app.routers.voice as voice_router
from app.database import SessionLocal
from app.models import CandidateProfile, RoleProfile, Session
from app.models.enums import SessionStatus
from app.policy import get_normal_policy
from app.voice import (
    ProviderNotConfigured,
    decide_turn_end,
    get_stt,
    get_tts,
    process_voice_turn,
)
from main import app

ENGINE = "phase14-test"
CANNED_ANSWER = (
    "I sharded the queue by customer id across 8 shards, cutting p99 "
    "latency from 900ms to 220ms."
)


async def fake_stt(audio: bytes) -> str:
    assert audio == b"fake-audio-frames"
    return CANNED_ANSWER


async def fake_tts(text: str) -> bytes:
    assert text.strip()
    return b"fake-mp3-bytes"


def make_session(db) -> Session:
    cand = CandidateProfile(
        raw_resume_text="phase14 resume",
        extracted_json={"skills": ["Python"], "projects": [], "claims": []},
    )
    role = RoleProfile(
        raw_jd_text="phase14 jd",
        extracted_json={
            "required_skills": ["Python"],
            "preferred_skills": [],
            "responsibilities": [],
            "seniority_signal": "unknown",
        },
    )
    db.add_all([cand, role])
    db.flush()
    session = Session(
        candidate_profile_id=cand.id,
        role_profile_id=role.id,
        mode="normal",
        policy_version=get_normal_policy().version,
        engine_version=ENGINE,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def main() -> None:
    # 1. Timing heuristic.
    assert decide_turn_end(0.0, 4.0, 4.0) is True
    assert decide_turn_end(0.0, 3.9, 4.0) is False
    assert decide_turn_end(10.0, 10.0, 4.0) is False
    print("turn-end heuristic ok")

    # 2. Factories fail helpfully without keys.
    for var in ("DEEPGRAM_API_KEY", "ELEVENLABS_API_KEY"):
        os.environ.pop(var, None)
    for factory in (get_stt, get_tts):
        try:
            factory()
        except ProviderNotConfigured as e:
            assert "https://" in str(e), e
        else:
            raise AssertionError(f"{factory} should raise without keys")
    print("provider key guards ok")

    db = SessionLocal()
    try:
        # 3. One spoken turn through the real engine with fake audio IO.
        session = make_session(db)
        out = asyncio.run(
            process_voice_turn(
                db,
                session,
                get_normal_policy(),
                b"fake-audio-frames",
                fake_stt,
                fake_tts,
            )
        )
        assert out["transcript"] == CANNED_ANSWER
        assert out["question"].strip() and out["audio"] == b"fake-mp3-bytes"
        assert out["claims_found"] >= 1
        db.refresh(session)
        assert session.turns[-1].text == out["question"]
        assert session.turns[-2].text == CANNED_ANSWER
        print(f"voice turn ok: state={out['state']} claims={out['claims_found']}")
        db.delete(session)
        db.commit()

        # 4. Full WS round trip with patched providers.
        session2 = make_session(db)
        voice_router.get_stt = lambda: FakeSTT()
        voice_router.get_tts = lambda: FakeTTS()
        try:
            client = TestClient(app)
            with client.websocket_connect(f"/session/{session2.id}/voice") as ws:
                ready = json.loads(ws.receive_text())
                assert ready["type"] == "ready", ready
                assert ready["silence_threshold_seconds"] >= 1
                ws.send_bytes(b"fake-audio-frames")
                ws.send_text(json.dumps({"type": "end_of_turn"}))
                answer = json.loads(ws.receive_text())
                assert answer["type"] == "answer", answer
                assert answer["transcript"] == CANNED_ANSWER
                question = json.loads(ws.receive_text())
                assert question["type"] == "question" and question["text"].strip()
                audio = json.loads(ws.receive_text())
                assert audio["type"] == "audio" and audio["data_b64"]
                print("WS round trip ok (answer+question+audio frames)")
        finally:
            voice_router.get_stt = get_stt
            voice_router.get_tts = get_tts
        db.refresh(session2)
        assert session2.status == SessionStatus.IN_PROGRESS
        print("CHECKPOINT 14 PASS: voice adapter round-trips, engine untouched")
    finally:
        for s in db.query(Session).filter(Session.engine_version == ENGINE).all():
            db.delete(s)
        db.commit()
        db.query(CandidateProfile).filter(
            CandidateProfile.raw_resume_text == "phase14 resume"
        ).delete(synchronize_session=False)
        db.query(RoleProfile).filter(RoleProfile.raw_jd_text == "phase14 jd").delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


class FakeSTT:
    async def transcribe(self, audio: bytes) -> str:
        return await fake_stt(audio)


class FakeTTS:
    async def synthesize(self, text: str) -> bytes:
        return await fake_tts(text)


if __name__ == "__main__":
    main()
