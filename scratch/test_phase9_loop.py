"""Phase 9 checkpoint: full text loop start -> answers -> close (real LLM).

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase9_loop.py``.
2 real answer cycles (extraction + proposal + question each), then a
deterministic close-path check via ctx override. Cleans up afterwards.
"""

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.interview import TransitionContext, answer_session
from app.interview.loop import ENGINE_VERSION
from app.models import CandidateProfile, RoleProfile, Session
from app.policy import get_normal_policy
from main import app

CANDIDATE_JSON = {
    "skills": ["Python", "PostgreSQL"],
    "projects": [{"name": "Queue shard", "description": "Sharded queue, cut p99."}],
    "claims": ["cut p99 latency"],
}
ROLE_JSON = {
    "required_skills": ["Python", "PostgreSQL", "system design"],
    "preferred_skills": [],
    "responsibilities": ["Build APIs"],
    "seniority_signal": "mid-level",
}

ANSWERS = [
    "I sharded the queue by customer id across 8 shards, which cut p99 "
    "latency from 900ms to 220ms.",
    "We measured with histogram metrics on each shard, comparing a week of "
    "baseline traffic against the rollout week.",
]


def seed_profiles() -> tuple[int, int]:
    db = SessionLocal()
    cand = CandidateProfile(raw_resume_text="phase9 resume", extracted_json=CANDIDATE_JSON)
    role = RoleProfile(raw_jd_text="phase9 jd", extracted_json=ROLE_JSON)
    db.add_all([cand, role])
    db.commit()
    ids = (cand.id, role.id)
    db.close()
    return ids


def cleanup() -> None:
    db = SessionLocal()
    for s in db.query(Session).filter(Session.engine_version == ENGINE_VERSION).all():
        db.delete(s)
    for c in db.query(CandidateProfile).filter(
        CandidateProfile.raw_resume_text == "phase9 resume"
    ).all():
        db.delete(c)
    for r in db.query(RoleProfile).filter(RoleProfile.raw_jd_text == "phase9 jd").all():
        db.delete(r)
    db.commit()
    db.close()


def main() -> None:
    policy = get_normal_policy()
    cand_id, role_id = seed_profiles()
    client = TestClient(app)

    try:
        # Start.
        r = client.post(
            "/session/start",
            json={"candidate_profile_id": cand_id, "role_profile_id": role_id},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        sid = body["session_id"]
        assert body["state"] == "OPENING" and body["question"].strip()
        print(f"started session {sid}: {body['question'][:100]}...")

        # Two real answer cycles through HTTP.
        for i, text in enumerate(ANSWERS):
            r = client.post(f"/session/{sid}/answer", json={"text": text})
            assert r.status_code == 200, r.text
            out = r.json()
            assert out["question"].strip(), out
            assert out["claims_found"] >= 1, out
            print(f"answer {i + 1}: state={out['state']} "
                  f"applied={out['transition_applied']} "
                  f"claims={out['claims_found']}")
            print(f"  next q: {out['question'][:110]}...")

        d = client.get(f"/session/{sid}").json()
        assert d["turns"] == 1 + 2 * len(ANSWERS), d
        assert d["claims"] >= 2, d
        assert d["status"] == "in_progress", d
        print(f"detail: state={d['state']} turns={d['turns']} claims={d['claims']}")

        # Deterministic close path (override ctx: full coverage + 45min).
        db = SessionLocal()
        session = db.query(Session).filter(Session.id == sid).first()
        close_ctx = TransitionContext(
            elapsed_minutes=float(policy.target_duration_minutes) + 5,
            projects_covered=policy.min_projects_covered,
            required_skills_covered=policy.min_required_skills_covered,
        )
        for _ in range(4):  # LLM may take a turn or two to propose CLOSING
            out = answer_session(db, session, policy, "Wrapping up.", close_ctx)
            db.refresh(session)
            if out["finished"]:
                break
        assert out["finished"] is True, out
        assert session.status.value == "completed", session.status
        assert session.ended_at is not None
        print(f"closed: {out['question'][:110]}...")
        db.close()

        # Answering a closed session is rejected.
        r = client.post(f"/session/{sid}/answer", json={"text": "hello?"})
        assert r.status_code == 409, r.text
        print("post-close answer correctly rejected (409)")

        # Unknown session + bad payloads.
        assert client.get("/session/999999").status_code == 404
        assert client.post("/session/999999/answer", json={"text": "x"}).status_code == 404
        print("CHECKPOINT 9 PASS: start -> answers -> close -> 409/404 guards")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
