"""Phase 7 checkpoint: LLM proposes, validator disposes (real LLM, 1 call).

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase7_proposal.py``.
Exits nonzero on failure; cleans up its test sessions afterwards.
"""

from app.database import SessionLocal
from app.extraction import persist_answer_claims
from app.interview import (
    InterviewState,
    StateMachine,
    TransitionContext,
    apply_proposal,
    context_for_session,
    propose_state,
    recent_claims_for_session,
)
from app.models import CandidateProfile, RoleProfile, Session, StateTransition, Turn
from app.models.enums import Speaker
from app.policy import get_normal_policy

FAKE_PARSED = {
    "claims": [
        {
            "claim_text": "Sharded the queue by customer id across 8 shards.",
            "category": "performance",
            "confidence": 0.9,
            "evidence": [
                {
                    "evidence_text": "partitioning across 8 shards",
                    "evidence_type": "supports",
                }
            ],
        },
        {
            "claim_text": "Cut p99 latency from 900ms to 220ms.",
            "category": "performance",
            "confidence": 0.85,
            "evidence": [
                {
                    "evidence_text": "p99 from 900ms to 220ms",
                    "evidence_type": "supports",
                }
            ],
        },
    ]
}


def make_session(db) -> Session:
    cand = CandidateProfile(
        raw_resume_text="phase7 test resume",
        extracted_json={"skills": [], "projects": [], "claims": []},
    )
    role = RoleProfile(
        raw_jd_text="phase7 test jd",
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
        engine_version="phase7-test",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def llm_rows(db, session_id: int) -> list[StateTransition]:
    return (
        db.query(StateTransition)
        .filter(
            StateTransition.session_id == session_id,
            StateTransition.proposed_by_llm.is_(True),
        )
        .order_by(StateTransition.id)
        .all()
    )


def main() -> None:
    policy = get_normal_policy()
    db = SessionLocal()
    try:
        session = make_session(db)
        turn = Turn(
            session_id=session.id,
            turn_index=1,
            speaker=Speaker.CANDIDATE,
            text="We sharded by customer id; p99 went 900ms to 220ms.",
        )
        db.add(turn)
        db.commit()
        db.refresh(turn)
        persist_answer_claims(
            db, session_id=session.id, turn_id=turn.id, parsed=FAKE_PARSED
        )

        machine = StateMachine(session.id, db, policy)
        assert machine.propose_transition("PROBING_CLAIM", "test setup")
        assert machine.current_state == InterviewState.PROBING_CLAIM

        # 1. Real LLM proposal goes through the validator, never around it.
        claims = recent_claims_for_session(db, session.id)
        assert len(claims) == 2
        ctx = context_for_session(db, session, policy)
        proposal, model_id = propose_state(machine.current_state, policy, claims, ctx)
        assert "proposed_state" in proposal, f"bad proposal: {proposal!r}"
        print(
            f"LLM proposed: {proposal.get('proposed_state')!r} "
            f"reason={str(proposal.get('reason'))[:120]!r} via {model_id}"
        )
        accepted = apply_proposal(machine, proposal, model_id, ctx)
        print(
            f"validator: {'ACCEPTED' if accepted else 'REJECTED'} "
            f"-> state={machine.current_state.value}"
        )
        assert isinstance(machine.current_state, InterviewState)
        rows = llm_rows(db, session.id)
        assert rows, "proposal was not persisted as proposed_by_llm"
        assert rows[-1].to_state == str(proposal.get("proposed_state"))

        # 2. Illegal early-CLOSING proposal is caught, state unchanged.
        before = machine.current_state
        illegal = {
            "proposed_state": "CLOSING",
            "target_claim_id": None,
            "reason": "test: close 1 minute in with zero coverage",
        }
        zero_ctx = TransitionContext(elapsed_minutes=1.0)
        assert apply_proposal(machine, illegal, "test-manual", zero_ctx) is False
        assert machine.current_state == before
        rej = llm_rows(db, session.id)[-1]
        assert rej.was_validated is False and rej.rejection_reason
        print(f"illegal CLOSING caught: {rej.rejection_reason[:100]}")

        # 3. Unknown state string is rejected, no crash.
        bogus = {"proposed_state": "NAPPING", "reason": "test"}
        assert apply_proposal(machine, bogus, "test-manual", zero_ctx) is False
        assert isinstance(machine.current_state, InterviewState)
        print("unknown state rejected without crash")

        # 4. Session continues sanely after rejections.
        if machine.current_state == InterviewState.CLOSING:
            print(
                "note: LLM legitimately closed; reopening fresh machine "
                "for continuation check"
            )
            session2 = make_session(db)
            machine = StateMachine(session2.id, db, policy)
            assert machine.propose_transition("PROBING_CLAIM", "setup")
        cont = {
            "proposed_state": "FOLLOWING_UP",
            "target_claim_id": claims[0].id,
            "reason": "test: dig into the sharding claim",
        }
        assert apply_proposal(machine, cont, "test-manual", zero_ctx) is True
        assert machine.current_state == InterviewState.FOLLOWING_UP
        print("continuation legal move accepted after rejections")

        print("CHECKPOINT 7 PASS: LLM proposes, validator disposes")
    finally:
        for s in (
            db.query(Session).filter(Session.engine_version == "phase7-test").all()
        ):
            db.delete(s)
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
