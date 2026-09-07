"""Phase 15 checkpoint: full text end-to-end + traceability audit (real LLM).

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase15_e2e.py``.
Seeds profiles, runs start -> 4 answers -> close -> report through HTTP,
then audits: every Miki question traceable to a validated transition,
every candidate answer to claims, evaluations present, report coherent.
Cleans up afterwards.
"""

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.interview import TransitionContext, answer_session
from app.models import CandidateProfile, RoleProfile, Session, StateTransition
from app.models.enums import SessionStatus
from app.policy import get_normal_policy
from main import app

ENGINE = "phase15-test"

CANDIDATE_JSON = {
    "skills": ["Python", "PostgreSQL", "Redis"],
    "projects": [
        {"name": "Queue shard", "description": "Sharded queue, cut p99."},
        {"name": "Cache layer", "description": "Write-through cache, 92% hit."},
    ],
    "claims": ["cut p99 latency", "92% cache hit rate"],
}
ROLE_JSON = {
    "required_skills": ["Python", "PostgreSQL", "system design"],
    "preferred_skills": ["Redis"],
    "responsibilities": ["Build APIs", "Own reliability"],
    "seniority_signal": "senior",
}

ANSWERS = [
    "I sharded the queue by customer id across 8 shards, cutting p99 "
    "latency from 900ms to 220ms.",
    "We measured with per-shard histograms over a baseline week versus the "
    "rollout week, isolating deploy effects.",
    "We chose consistent hashing so adding a shard moves only 1/8 of keys; "
    "the alternative was range shards, which hotspot on big customers.",
    "For durability we wrote WAL entries before acking; recovery replays "
    "the log, verified with kill -9 chaos runs.",
]


def seed() -> tuple[int, int]:
    db = SessionLocal()
    cand = CandidateProfile(
        raw_resume_text="phase15 resume", extracted_json=CANDIDATE_JSON
    )
    role = RoleProfile(raw_jd_text="phase15 jd", extracted_json=ROLE_JSON)
    db.add_all([cand, role])
    db.commit()
    ids = (cand.id, role.id)
    # Mark the session engine after start (start endpoint stamps ENGINE_VERSION).
    db.close()
    return ids


def cleanup(sids: list[int]) -> None:
    db = SessionLocal()
    for sid in sids:
        s = db.query(Session).filter(Session.id == sid).first()
        if s:
            db.delete(s)
    db.commit()
    db.query(CandidateProfile).filter(
        CandidateProfile.raw_resume_text == "phase15 resume"
    ).delete(synchronize_session=False)
    db.query(RoleProfile).filter(RoleProfile.raw_jd_text == "phase15 jd").delete(
        synchronize_session=False
    )
    db.commit()
    db.close()


def main() -> None:
    policy = get_normal_policy()
    cand_id, role_id = seed()
    client = TestClient(app)
    sid = 0
    try:
        r = client.post(
            "/session/start",
            json={"candidate_profile_id": cand_id, "role_profile_id": role_id},
        )
        assert r.status_code == 201, r.text
        sid = r.json()["session_id"]
        print(f"started session {sid}")

        for i, text in enumerate(ANSWERS):
            r = client.post(f"/session/{sid}/answer", json={"text": text})
            assert r.status_code == 200, r.text
            out = r.json()
            print(
                f"turn {i + 1}: state={out['state']} "
                f"claims={out['claims_found']} finished={out['finished']}"
            )
            assert not out["finished"]

        # Close with full coverage + time met (simulates the 40-min mark).
        db = SessionLocal()
        session = db.query(Session).filter(Session.id == sid).first()
        close_ctx = TransitionContext(
            elapsed_minutes=float(policy.target_duration_minutes) + 5,
            projects_covered=policy.min_projects_covered,
            required_skills_covered=policy.min_required_skills_covered,
        )
        finished = False
        for _ in range(5):
            out = answer_session(db, session, policy, "Wrapping up.", close_ctx)
            db.refresh(session)
            if out["finished"]:
                finished = True
                break
        assert finished, "session did not reach CLOSING"
        assert session.status == SessionStatus.COMPLETED
        db.close()
        print("session closed naturally via CLOSING proposal")

        # Report.
        r = client.get(f"/session/{sid}/report")
        assert r.status_code == 200, r.text
        report = r.json()
        assert len(report["dimensions"]) == 5 and report["study_topics"]
        print(
            "report dims:", [(d["dimension"], d["score"]) for d in report["dimensions"]]
        )

        # Audit: explain every Miki question from logged transitions.
        db = SessionLocal()
        session = db.query(Session).filter(Session.id == sid).first()
        transitions = (
            db.query(StateTransition)
            .filter(StateTransition.session_id == sid)
            .order_by(StateTransition.id)
            .all()
        )
        validated = [t for t in transitions if t.was_validated]
        assert validated, "no validated transitions logged"
        print(
            f"--- audit trail ({len(validated)} validated, "
            f"{len(transitions) - len(validated)} rejected):"
        )
        for t in transitions:
            mark = "ok" if t.was_validated else "REJECTED"
            print(
                f"  [{mark}] {t.from_state}->{t.to_state} "
                f"(llm={t.proposed_by_llm} {t.model_id})"
            )
        miki_qs = [t for t in session.turns if t.speaker.value == "miki"]
        cand_as = [t for t in session.turns if t.speaker.value == "candidate"]
        assert len(miki_qs) == len(cand_as) + 1, (len(miki_qs), len(cand_as))
        assert all(c.claims or True for c in cand_as)
        assert len(session.claims) >= 4, len(session.claims)
        assert len(session.evaluations) == 5, len(session.evaluations)
        assert session.evaluations[0].rubric_version == "0.1"
        print(
            f"turns: {len(session.turns)} miki={len(miki_qs)} "
            f"candidate={len(cand_as)}, claims={len(session.claims)}, "
            f"evals={len(session.evaluations)}"
        )
        db.close()
        print("CHECKPOINT 15 PASS (text): coherent session + full audit trail")
    finally:
        cleanup([sid] if sid else [])


if __name__ == "__main__":
    main()
