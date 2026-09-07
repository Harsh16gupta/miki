"""Phase 12 calibration runner: evaluator vs blind hand scores.

Run with ``PYTHONPATH=. venv/bin/python scratch/test_phase12_calibration.py``.
8 vignettes x 1 evaluation call. Prints per-dimension mean absolute error.
Bar: MAE <= 1.0 per dimension. On systematic gaps, adjust the rubric or
evaluator prompt (vignette hand scores stay fixed), then re-run.
"""

from app.database import SessionLocal
from app.evaluation import evaluate_session, get_normal_rubric
from app.models import CandidateProfile, Claim, Evidence, RoleProfile, Session, Turn
from app.models.enums import EvidenceType, SessionStatus, Speaker
from app.policy import get_normal_policy
from calibration.vignettes import VIGNETTES

ENGINE = "phase12-test"
BAR = 1.0


def build_vignette(db, vignette: dict) -> Session:
    cand = CandidateProfile(
        raw_resume_text=f"calibration {vignette['name']}",
        extracted_json={"skills": [], "projects": [], "claims": []},
    )
    role = RoleProfile(
        raw_jd_text="calibration jd",
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
    for idx, (speaker, text) in enumerate(vignette["turns"], start=1):
        db.add(
            Turn(
                session_id=session.id,
                turn_index=idx,
                speaker=Speaker.MIKI if speaker == "miki" else Speaker.CANDIDATE,
                text=text,
            )
        )
    db.flush()
    turn_ids = [
        t.id
        for t in db.query(Turn)
        .filter(Turn.session_id == session.id)
        .order_by(Turn.turn_index)
    ]
    for item in vignette["claims"]:
        claim = Claim(
            session_id=session.id,
            turn_id=turn_ids[item["turn"] - 1],
            claim_text=item["text"],
            category=item["category"],
            confidence=item["confidence"],
        )
        db.add(claim)
        db.flush()
        for ev_text, ev_type in item["evidence"]:
            db.add(
                Evidence(
                    claim_id=claim.id,
                    turn_id=claim.turn_id,
                    evidence_text=ev_text,
                    evidence_type=EvidenceType(ev_type),
                )
            )
    db.commit()
    db.refresh(session)
    return session


def main() -> None:
    rubric = get_normal_rubric()
    dims = [d.name for d in rubric.dimensions]
    errors: dict[str, list[float]] = {d: [] for d in dims}
    db = SessionLocal()
    try:
        for vignette in VIGNETTES:
            session = build_vignette(db, vignette)
            rows = {r.dimension: r.score for r in evaluate_session(db, session, rubric)}
            print(f"--- {vignette['name']}")
            for dim in dims:
                hand = vignette["hand_scores"][dim]
                got = rows[dim]
                err = abs(got - hand)
                errors[dim].append(err)
                flag = "" if err <= BAR else "  <-- DIVERGED"
                print(f"  {dim}: hand={hand} eval={got:.1f} err={err:.1f}{flag}")
        print("--- mean absolute error per dimension:")
        failed = []
        for dim in dims:
            mae = sum(errors[dim]) / len(errors[dim])
            status = "ok" if mae <= BAR else "OVER BAR"
            if mae > BAR:
                failed.append(dim)
            print(f"  {dim}: MAE={mae:.2f} [{status}]")
        if failed:
            raise SystemExit(f"CHECKPOINT 12 FAILED on: {failed}")
        print("CHECKPOINT 12 PASS: evaluator aligned with hand scores")
    finally:
        for s in db.query(Session).filter(Session.engine_version == ENGINE).all():
            db.delete(s)
        db.commit()
        db.query(CandidateProfile).filter(
            CandidateProfile.raw_resume_text.like("calibration %")
        ).delete(synchronize_session=False)
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
