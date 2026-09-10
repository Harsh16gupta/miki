"""Phase 11 checkpoint: rubric scoring with cited evidence (real LLM, 1 call).

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase11_eval.py``.
Builds a fixed 4-turn session by hand (no loop calls), evaluates it, and
checks every row: known dimension, in-scale score, refs point at real rows.
Cleans up afterwards. Read the printed scores manually.
"""

from app.database import SessionLocal
from app.evaluation import evaluate_session, get_normal_rubric, ref_details
from app.models import CandidateProfile, Claim, Evidence, RoleProfile, Session, Turn
from app.models.enums import EvidenceType, SessionStatus, Speaker
from app.policy import get_normal_policy


def build_session(db) -> Session:
    cand = CandidateProfile(
        raw_resume_text="phase11 resume",
        extracted_json={"skills": ["Python"], "projects": [], "claims": []},
    )
    role = RoleProfile(
        raw_jd_text="phase11 jd",
        extracted_json={
            "required_skills": ["Python"],
            "preferred_skills": [],
            "responsibilities": ["Build APIs"],
            "seniority_signal": "mid-level",
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
        engine_version="phase11-test",
    )
    db.add(session)
    db.flush()
    t1 = Turn(
        session_id=session.id,
        turn_index=1,
        speaker=Speaker.MIKI,
        text="How did you design the cache invalidation?",
    )
    t2 = Turn(
        session_id=session.id,
        turn_index=2,
        speaker=Speaker.CANDIDATE,
        text="We used write-through with a 5-minute TTL, measured "
        "hit rate at 92% with per-key metrics.",
    )
    t3 = Turn(
        session_id=session.id,
        turn_index=3,
        speaker=Speaker.MIKI,
        text="Why write-through over write-back here?",
    )
    t4 = Turn(
        session_id=session.id,
        turn_index=4,
        speaker=Speaker.CANDIDATE,
        text="Honestly it was just simpler, not much thought.",
    )
    db.add_all([t1, t2, t3, t4])
    db.flush()
    claim = Claim(
        session_id=session.id,
        turn_id=t2.id,
        claim_text="Hit rate at 92% with per-key metrics.",
        category="performance",
        confidence=0.9,
    )
    db.add(claim)
    db.flush()
    db.add(
        Evidence(
            claim_id=claim.id,
            turn_id=t2.id,
            evidence_text="measured hit rate at 92%",
            evidence_type=EvidenceType.SUPPORTS,
        )
    )
    db.add(
        Evidence(
            claim_id=claim.id,
            turn_id=t4.id,
            evidence_text="just simpler, not much thought",
            evidence_type=EvidenceType.VAGUE,
        )
    )
    db.commit()
    db.refresh(session)
    return session


def main() -> None:
    rubric = get_normal_rubric()
    assert len(rubric.dimensions) == 5, len(rubric.dimensions)
    db = SessionLocal()
    try:
        session = build_session(db)
        rows = evaluate_session(db, session, rubric)
        assert len(rows) == 5, f"expected 5 rows, got {len(rows)}"
        assert {r.dimension for r in rows} == {d.name for d in rubric.dimensions}
        for row in sorted(rows, key=lambda r: r.dimension):
            assert rubric.scale_min <= row.score <= rubric.scale_max, row.score
            assert row.rubric_version == rubric.version
            refs = row.evidence_refs
            assert set(refs) == {"claim_ids", "evidence_ids", "turn_ids"}, refs
            assert refs["turn_ids"], f"{row.dimension}: no turn cited"
            print(f"--- {row.dimension}: {row.score}")
            for key in ("claims", "evidence", "turns"):
                for item in ref_details(db, row)[key]:
                    print(f"  [{key} {item['id']}] {item['text'][:90]}")
        print("CHECKPOINT 11 PASS: 5 scored dimensions, all evidence-cited")
    finally:
        for s in (
            db.query(Session).filter(Session.engine_version == "phase11-test").all()
        ):
            db.delete(s)
        db.commit()
        db.query(CandidateProfile).filter(
            CandidateProfile.raw_resume_text == "phase11 resume"
        ).delete(synchronize_session=False)
        db.query(RoleProfile).filter(RoleProfile.raw_jd_text == "phase11 jd").delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
