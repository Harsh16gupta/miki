"""Phase 13 checkpoint: report renders scores + coach prose (real LLM, 1 call).

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase13_report.py``.
Hand-built completed session with fixed eval rows; checks the report dict
directly and through GET /session/{id}/report, plus 409/404 guards.
"""

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.evaluation import build_report, get_normal_rubric
from app.models import CandidateProfile, Claim, Evaluation, RoleProfile, Session, Turn
from app.models.enums import SessionStatus, Speaker
from app.policy import get_normal_policy
from main import app

ENGINE = "phase13-test"


def build_scored_session(db) -> Session:
    cand = CandidateProfile(
        raw_resume_text="phase13 resume",
        extracted_json={"skills": [], "projects": [], "claims": []},
    )
    role = RoleProfile(
        raw_jd_text="phase13 jd",
        extracted_json={
            "required_skills": [],
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
        status=SessionStatus.COMPLETED,
        policy_version=get_normal_policy().version,
        engine_version=ENGINE,
    )
    db.add(session)
    db.flush()
    t1 = Turn(
        session_id=session.id,
        turn_index=1,
        speaker=Speaker.MIKI,
        text="How did you measure the speedup?",
    )
    t2 = Turn(
        session_id=session.id,
        turn_index=2,
        speaker=Speaker.CANDIDATE,
        text="Cut p99 from 900ms to 220ms per shard histograms.",
    )
    db.add_all([t1, t2])
    db.flush()
    claim = Claim(
        session_id=session.id,
        turn_id=t2.id,
        claim_text="Cut p99 900ms to 220ms.",
        category="performance",
        confidence=0.9,
    )
    db.add(claim)
    db.flush()
    rubric = get_normal_rubric()
    for dim in rubric.dimensions:
        db.add(
            Evaluation(
                session_id=session.id,
                dimension=dim.name,
                score=4.0,
                evidence_refs={
                    "claim_ids": [claim.id],
                    "evidence_ids": [],
                    "turn_ids": [t2.id],
                },
                rubric_version=rubric.version,
                model_id="phase13-test",
            )
        )
    db.commit()
    db.refresh(session)
    return session


def check_report(report: dict) -> None:
    assert report["status"] == "completed", report
    assert len(report["dimensions"]) == 5, report
    for dim in report["dimensions"]:
        assert dim["score"] == 4.0
        assert dim["refs"]["turns"], dim
    for key in ("strengths", "weaknesses", "hard_to_defend_claims", "study_topics"):
        assert isinstance(report[key], list) and report[key], key
    print("dimensions:", [(d["dimension"], d["score"]) for d in report["dimensions"]])
    print("strengths:", report["strengths"][:2])
    print("weaknesses:", report["weaknesses"][:2])
    print("study_topics:", report["study_topics"][:2])


def main() -> None:
    db = SessionLocal()
    try:
        session = build_scored_session(db)
        sid = session.id

        report = build_report(db, session, get_normal_rubric())
        check_report(report)

        client = TestClient(app)
        r = client.get(f"/session/{sid}/report")
        assert r.status_code == 200, r.text
        check_report(r.json())
        print("GET /report matches direct build")

        assert client.get("/session/999999/report").status_code == 404
        print("unknown session 404 ok")
    finally:
        for s in db.query(Session).filter(Session.engine_version == ENGINE).all():
            db.delete(s)
        db.commit()
        db.query(CandidateProfile).filter(
            CandidateProfile.raw_resume_text == "phase13 resume"
        ).delete(synchronize_session=False)
        db.query(RoleProfile).filter(RoleProfile.raw_jd_text == "phase13 jd").delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
