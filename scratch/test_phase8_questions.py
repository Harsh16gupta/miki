"""Phase 8 checkpoint: generated questions are coherent + persisted (real LLM).

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase8_questions.py``.
Uses the question_generation model (3 calls); exits nonzero on failure.
Cleans up its test sessions afterwards. Read the printed questions manually.
"""

from app.database import SessionLocal
from app.interview import (
    InterviewState,
    generate_question,
    persist_miki_turn,
)
from app.models import CandidateProfile, Claim, RoleProfile, Session, Turn
from app.models.enums import Speaker
from app.policy import get_normal_policy

CANDIDATE_JSON = {
    "skills": ["Python", "PostgreSQL", "FastAPI"],
    "projects": [
        {
            "name": "RAG pipeline at Acme",
            "description": "Built RAG pipeline, cut latency 40%.",
        }
    ],
    "claims": ["reduced latency by 40%"],
}
ROLE_JSON = {
    "required_skills": ["Python", "PostgreSQL", "system design"],
    "preferred_skills": ["Langfuse"],
    "responsibilities": ["Build APIs"],
    "seniority_signal": "senior",
}


def make_session(db) -> Session:
    cand = CandidateProfile(
        raw_resume_text="phase8 test resume", extracted_json=CANDIDATE_JSON
    )
    role = RoleProfile(raw_jd_text="phase8 test jd", extracted_json=ROLE_JSON)
    db.add_all([cand, role])
    db.flush()
    session = Session(
        candidate_profile_id=cand.id,
        role_profile_id=role.id,
        mode="normal",
        policy_version=get_normal_policy().version,
        engine_version="phase8-test",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def check_question(label: str, text: str, forbidden: tuple[str, ...] = ()) -> None:
    assert text and text.strip(), f"{label}: empty question"
    assert len(text) < 2000, f"{label}: absurdly long ({len(text)} chars)"
    lowered = text.lower()
    for marker in forbidden:
        assert marker not in lowered, f"{label}: looks like JSON, got: {text[:120]!r}"
    print(f"--- {label}:\n{text}\n")


def main() -> None:
    policy = get_normal_policy()
    db = SessionLocal()
    try:
        session = make_session(db)
        no_json = ("{", "}", '"proposed_state"', '"claim_text"')

        # 1. Opening question: broad warmer, no claim context.
        q1, m1 = generate_question(
            InterviewState.OPENING, policy, CANDIDATE_JSON, ROLE_JSON
        )
        check_question("opening", q1, no_json)
        t1 = persist_miki_turn(db, session_id=session.id, text=q1)
        assert t1.speaker == Speaker.MIKI and t1.turn_index == 1, t1
        print(f"(via {m1}, persisted turn id={t1.id} index={t1.turn_index})")

        # 2. Probing question aimed at one stored claim.
        cand_turn = Turn(
            session_id=session.id,
            turn_index=2,
            speaker=Speaker.CANDIDATE,
            text="At Acme I built the RAG pipeline and cut latency 40%.",
        )
        db.add(cand_turn)
        db.commit()
        db.refresh(cand_turn)
        claim = Claim(
            session_id=session.id,
            turn_id=cand_turn.id,
            claim_text="Reduced latency by 40% on the RAG pipeline.",
            category="performance",
            confidence=0.9,
        )
        db.add(claim)
        db.commit()
        db.refresh(claim)
        q2, m2 = generate_question(
            InterviewState.PROBING_CLAIM,
            policy,
            CANDIDATE_JSON,
            ROLE_JSON,
            target_claim=claim,
            recent_turns=[f"Miki: {q1}", f"Candidate: {cand_turn.text}"],
        )
        check_question("probing", q2, no_json)
        lowered = q2.lower()
        assert any(
            w in lowered for w in ("40", "latency", "measur", "how", "rag", "pipeline")
        ), f"probing question ignores the claim: {q2[:150]!r}"
        t2 = persist_miki_turn(db, session_id=session.id, text=q2)
        assert t2.turn_index == 3, t2
        print(f"(via {m2}, persisted turn id={t2.id} index={t2.turn_index})")

        # 3. Follow-up digging into a vague answer.
        q3, m3 = generate_question(
            InterviewState.FOLLOWING_UP,
            policy,
            CANDIDATE_JSON,
            ROLE_JSON,
            target_claim=claim,
            recent_turns=[
                f"Miki: {q2}",
                "Candidate: It was pretty scalable with good practices.",
            ],
        )
        check_question("follow-up", q3, no_json)
        t3 = persist_miki_turn(db, session_id=session.id, text=q3)
        assert t3.turn_index == 4, t3
        print(f"(via {m3}, persisted turn id={t3.id} index={t3.turn_index})")

        n_miki = (
            db.query(Turn)
            .filter(Turn.session_id == session.id, Turn.speaker == Speaker.MIKI)
            .count()
        )
        assert n_miki == 3, f"expected 3 miki turns, got {n_miki}"
        print("CHECKPOINT 8 PASS: coherent questions persisted as miki turns")
    finally:
        for s in (
            db.query(Session).filter(Session.engine_version == "phase8-test").all()
        ):
            db.delete(s)
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
