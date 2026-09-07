"""Phase 10 checkpoint: scripted regression sequences (real LLM, cheap models).

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase10_regression.py``.
5 sequences x ~2 answers through answer_session. Fails loudly on mismatch;
rerun once before touching prompts (LLM variance). Cleans up afterwards.
"""

from app.database import SessionLocal
from app.interview import answer_session
from app.interview.states import InterviewState
from app.models import CandidateProfile, RoleProfile, Session, StateTransition
from app.models.enums import SessionStatus
from app.policy import get_normal_policy

ENGINE = "phase10-test"

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

STRONG = (
    "I sharded the queue by customer id across 8 shards, cutting p99 latency "
    "from 900ms to 220ms, verified by per-shard histogram metrics."
)
STRONG2 = (
    "We picked consistent hashing for rebalance cost: adding a shard moves "
    "only 1/8 of keys, measured rebalance at under 30 seconds in staging."
)
STRONG3 = (
    "For durability we wrote WAL entries before acking, so a crash loses "
    "nothing; recovery replays the log, verified with kill -9 chaos runs."
)
WEAK = (
    "Yeah it was pretty scalable and fast, we used good practices and the "
    "team worked well together on it."
)
WEAK2 = "Hmm, I don't remember exactly, I think it was fine performance-wise."
CONTRA = (
    "Actually we never sharded anything, it stayed one Postgres table and "
    "latency was around 900ms the whole time."
)


def make_session(db) -> Session:
    cand = CandidateProfile(raw_resume_text="p10 resume", extracted_json=CANDIDATE_JSON)
    role = RoleProfile(raw_jd_text="p10 jd", extracted_json=ROLE_JSON)
    db.add_all([cand, role])
    db.flush()
    policy = get_normal_policy()
    session = Session(
        candidate_profile_id=cand.id,
        role_profile_id=role.id,
        mode="normal",
        policy_version=policy.version,
        engine_version=ENGINE,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def run_answers(db, session, answers: list[str]) -> list[dict]:
    policy = get_normal_policy()
    outs = []
    for text in answers:
        outs.append(answer_session(db, session, policy, text))
        db.refresh(session)
    return outs


def validated_states(db, session_id: int) -> list[str]:
    return [
        r.to_state
        for r in db.query(StateTransition)
        .filter(
            StateTransition.session_id == session_id,
            StateTransition.was_validated.is_(True),
        )
        .order_by(StateTransition.id)
        .all()
    ]


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"[{'ok' if cond else 'MISMATCH'}] {label} {detail}")
    if not cond:
        raise AssertionError(f"regression failed: {label} {detail}")


def main() -> None:
    db = SessionLocal()
    try:
        # A: probe-worthy claim leaves OPENING with solid claims.
        a = make_session(db)
        outs = run_answers(db, a, [STRONG])
        db.refresh(a)
        check(
            "A probe-worthy: state=PROBING_CLAIM",
            outs[-1]["state"] == "PROBING_CLAIM",
            outs[-1]["state"],
        )
        check("A probe-worthy: claims found", outs[-1]["claims_found"] >= 1)
        check("A session alive", a.status == SessionStatus.IN_PROGRESS)

        # B: vague answer draws a follow-up or low-confidence claims.
        b = make_session(db)
        outs = run_answers(db, b, [WEAK])
        db.refresh(b)
        b_claims = b.claims
        vague_signal = (
            (outs[-1]["state"] == InterviewState.FOLLOWING_UP.value)
            or (b_claims and all(c.confidence < 0.5 for c in b_claims))
            or (
                any(
                    e.evidence_type.value == "vague"
                    for c in b_claims
                    for e in c.evidence_items
                )
            )
        )
        check(
            "B vague: follow-up or low-conf/vague",
            bool(vague_signal),
            f"state={outs[-1]['state']}",
        )
        outs = run_answers(db, b, [STRONG])
        check("B recovers on strong answer", outs[-1]["state"] != "CLOSING")

        # C: three strong answers escalate.
        c = make_session(db)
        run_answers(db, c, [STRONG, STRONG2, STRONG3])
        states = validated_states(db, c.id)
        check("C strong x3 escalates", "ESCALATING" in states, str(states))

        # D: two weak answers must NOT escalate.
        d = make_session(db)
        run_answers(db, d, [WEAK, WEAK2])
        db.refresh(d)
        states = validated_states(db, d.id)
        check("D weak x2 never escalates", "ESCALATING" not in states, str(states))
        check("D session alive", d.status == SessionStatus.IN_PROGRESS)
        check("D never closes early", "CLOSING" not in states, str(states))

        # E: contradiction is captured as claims on that turn.
        e = make_session(db)
        run_answers(db, e, [STRONG])
        outs = run_answers(db, e, [CONTRA])
        db.refresh(e)
        check("E contradiction yields claims", outs[-1]["claims_found"] >= 1)
        check("E session alive", e.status == SessionStatus.IN_PROGRESS)

        print("CHECKPOINT 10 PASS: 5 regression sequences behave per policy")
    finally:
        for s in db.query(Session).filter(Session.engine_version == ENGINE).all():
            db.delete(s)
        db.commit()
        db.query(CandidateProfile).filter(
            CandidateProfile.raw_resume_text == "p10 resume"
        ).delete(synchronize_session=False)
        db.query(RoleProfile).filter(RoleProfile.raw_jd_text == "p10 jd").delete(
            synchronize_session=False
        )
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
