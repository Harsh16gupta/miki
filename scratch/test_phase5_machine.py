"""Phase 5 checkpoint: hardcoded legal/illegal transitions, zero LLM.

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase5_machine.py``.
Exits nonzero on any mismatch; cleans up its test sessions afterwards.
"""

from app.database import SessionLocal
from app.interview import InterviewState, StateMachine, TransitionContext
from app.models import CandidateProfile, RoleProfile, Session, StateTransition
from app.policy import get_normal_policy

PASS = "PASS"
FAIL = "FAIL"
results: list[tuple[str, bool, bool]] = []


def check(label: str, got: bool, want: bool) -> None:
    ok = got == want
    results.append((label, got, want))
    print(f"[{'ok' if ok else 'MISMATCH'}] {label}: got={got} want={want}")


def make_session(db) -> Session:
    cand = CandidateProfile(
        raw_resume_text="phase5 test resume",
        extracted_json={"skills": [], "projects": [], "claims": []},
    )
    role = RoleProfile(
        raw_jd_text="phase5 test jd",
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
        engine_version="phase5-test",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def main() -> None:
    policy = get_normal_policy()
    db = SessionLocal()
    try:
        sess_a = make_session(db)
        m = StateMachine(sess_a.id, db, policy)
        assert m.current_state == InterviewState.OPENING

        check(
            "A1 OPENING->PROBING_CLAIM legal",
            m.propose_transition("PROBING_CLAIM", "open"),
            True,
        )
        check(
            "A2 PROBING_CLAIM->FOLLOWING_UP legal",
            m.propose_transition(InterviewState.FOLLOWING_UP, "probe"),
            True,
        )
        check(
            "A3 FOLLOWING_UP->FOLLOWING_UP ok",
            m.propose_transition("FOLLOWING_UP", "dig", TransitionContext()),
            True,
        )
        check(
            "A4 FOLLOWING_UP over max followups rejected",
            m.propose_transition(
                "FOLLOWING_UP",
                "too deep",
                TransitionContext(
                    followups_on_current_claim=policy.max_followups_per_claim
                ),
            ),
            False,
        )
        assert m.current_state == InterviewState.FOLLOWING_UP, (
            "state must not move on reject"
        )
        check(
            "A5 early CLOSING rejected",
            m.propose_transition(
                "CLOSING", "too soon", TransitionContext(elapsed_minutes=5.0)
            ),
            False,
        )
        check(
            "A6 FOLLOWING_UP->ESCALATING legal",
            m.propose_transition("ESCALATING", "strong"),
            True,
        )
        check(
            "A7 ESCALATING->DE_ESCALATING illegal",
            m.propose_transition("DE_ESCALATING", "skip"),
            False,
        )
        check(
            "A8 ESCALATING->REDIRECTING legal",
            m.propose_transition("REDIRECTING", "pivot"),
            True,
        )
        check(
            "A9 REDIRECTING->ESCALATING illegal",
            m.propose_transition("ESCALATING", "back"),
            False,
        )
        check(
            "A10 REDIRECTING->PROBING_CLAIM legal",
            m.propose_transition("PROBING_CLAIM", "next claim"),
            True,
        )
        check("A11 unknown state rejected", m.propose_transition("BOGUS", "???"), False)

        sess_b = make_session(db)
        n = StateMachine(sess_b.id, db, policy)
        check(
            "B1 OPENING->CLOSING illegal",
            n.propose_transition("CLOSING", "jump"),
            False,
        )
        check(
            "B2 OPENING->PROBING_CLAIM legal",
            n.propose_transition("PROBING_CLAIM", "open"),
            True,
        )
        full = TransitionContext(
            elapsed_minutes=float(policy.target_duration_minutes) + 5,
            projects_covered=policy.min_projects_covered,
            required_skills_covered=policy.min_required_skills_covered,
        )
        check(
            "B3 covered CLOSING accepted",
            n.propose_transition("CLOSING", "wrap", full),
            True,
        )
        check(
            "B4 CLOSING terminal",
            n.propose_transition("PROBING_CLAIM", "reopen"),
            False,
        )

        rows = (
            db.query(StateTransition)
            .filter(StateTransition.session_id.in_([sess_a.id, sess_b.id]))
            .order_by(StateTransition.id)
            .all()
        )
        n_accepted = sum(1 for r in rows if r.was_validated)
        n_rejected = sum(1 for r in rows if not r.was_validated)
        bad_reject = [
            r.id for r in rows if not r.was_validated and not r.rejection_reason
        ]
        bad_accept = [r.id for r in rows if r.was_validated and r.rejection_reason]
        print(f"rows={len(rows)} accepted={n_accepted} rejected={n_rejected}")
        assert len(rows) == len(results), (
            f"expected {len(results)} rows, got {len(rows)}"
        )
        assert not bad_reject, f"rejected rows missing reason: {bad_reject}"
        assert not bad_accept, f"accepted rows with reason: {bad_accept}"

        mismatches = [label for label, got, want in results if got != want]
        if mismatches:
            raise SystemExit(f"CHECKPOINT 5 FAILED: {mismatches}")

        print(f"CHECKPOINT 5 {PASS}: validator + persistence correct")
    finally:
        for s in (
            db.query(Session).filter(Session.engine_version == "phase5-test").all()
        ):
            db.delete(s)
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
