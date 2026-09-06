"""Phase 6 checkpoint: claim/evidence extraction on fake answers (real LLM).

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase6_extraction.py``.
Uses the cheap extraction model; exits nonzero on structural failure.
Cleans up its test sessions afterwards. Inspect the printed claims manually.
"""

from app.database import SessionLocal
from app.extraction import extract_answer_claims, persist_answer_claims
from app.models import CandidateProfile, RoleProfile, Session, Turn
from app.models.enums import Speaker
from app.policy import get_normal_policy

CASES = [
    {
        "label": "strong specific",
        "answer": (
            "We handled 10k requests per second by partitioning the queue by "
            "customer id across 8 shards, which cut p99 latency from 900ms to "
            "220ms. I owned the partitioning design and the rollout."
        ),
        "recent": ["Miki: How did you scale the queue?"],
        "resume": ["reduced latency by 40%"],
        "expect_claims": True,
    },
    {
        "label": "vague",
        "answer": (
            "Yeah so the system was, you know, pretty scalable and we made "
            "things faster using good practices and teamwork."
        ),
        "recent": ["Miki: How did you scale the queue?"],
        "resume": ["reduced latency by 40%"],
        "expect_claims": False,  # ideally empty or low-confidence
    },
    {
        "label": "contradicting",
        "answer": (
            "Actually we never partitioned anything, it was a single Postgres "
            "table the whole time and latency stayed around 900ms."
        ),
        "recent": [
            "Miki: How did you scale the queue?",
            "Candidate: We handled 10k rps by partitioning across 8 shards.",
        ],
        "resume": ["reduced latency by 40%"],
        "expect_claims": True,
    },
    {
        "label": "mixed two topics",
        "answer": (
            "I set up CI with GitHub Actions so deploys went from weekly to "
            "daily. On call I also debugged a memory leak in the worker by "
            "profiling heap dumps, which stopped the OOM crashes."
        ),
        "recent": ["Miki: Tell me about your DevOps and on-call work."],
        "resume": [],
        "expect_claims": True,
    },
]


def make_session(db) -> Session:
    cand = CandidateProfile(
        raw_resume_text="phase6 test resume",
        extracted_json={"skills": [], "projects": [], "claims": []},
    )
    role = RoleProfile(
        raw_jd_text="phase6 test jd",
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
        policy_version=get_normal_policy().version,
        engine_version="phase6-test",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def main() -> None:
    db = SessionLocal()
    try:
        session = make_session(db)
        turn_index = 0
        for case in CASES:
            turn_index += 1
            turn = Turn(
                session_id=session.id,
                turn_index=turn_index,
                speaker=Speaker.CANDIDATE,
                text=case["answer"],
            )
            db.add(turn)
            db.commit()
            db.refresh(turn)

            parsed = extract_answer_claims(
                case["answer"],
                recent_turns=case["recent"],
                resume_claims=case["resume"],
            )
            assert isinstance(parsed.get("claims"), list), f"no claims list: {parsed!r}"
            claims = persist_answer_claims(
                db, session_id=session.id, turn_id=turn.id, parsed=parsed
            )
            # Structural checks on every persisted row.
            for claim in claims:
                assert claim.turn_id == turn.id
                assert claim.session_id == session.id
                assert 0.0 <= claim.confidence <= 1.0
                assert claim.claim_text.strip()
                for ev in claim.evidence_items:
                    assert ev.turn_id == turn.id
                    valid = ("supports", "contradicts", "vague")
                    assert ev.evidence_type.value in valid

            print(f"--- {case['label']}: {len(claims)} claim(s)")
            for claim in claims:
                print(f"  [{claim.category} conf={claim.confidence:.2f}]")
                print(f"  {claim.claim_text[:160]}")
                for ev in claim.evidence_items:
                    print(f"    ({ev.evidence_type.value}) {ev.evidence_text[:100]}")
            if case["expect_claims"]:
                assert claims, f"expected claims for case {case['label']!r}, got none"
            else:
                vague_ok = not claims or all(c.confidence < 0.4 for c in claims)
                print(f"  vague-case low-confidence-or-empty: {vague_ok}")

        print("CHECKPOINT 6 PASS: claims/evidence extracted + persisted")
    finally:
        leftover = (
            db.query(Session).filter(Session.engine_version == "phase6-test").all()
        )
        for s in leftover:
            db.delete(s)
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
