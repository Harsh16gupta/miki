"""Evidence-grounded session evaluator (Phase 11).

One LLM call scores every rubric dimension against the full transcript plus
extracted claims/evidence. Each score must cite claim/evidence/turn ids from
this session — ids are validated before anything is persisted, so a
hallucinated citation fails loudly instead of landing in the database.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.evaluation.rubric import Rubric
from app.llm.router import call_llm
from app.models import Claim, Evaluation, Evidence, Session, Turn

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an evidence-grounded interview evaluator. Score the session on "
    "each rubric dimension and return a single JSON object with one key "
    '"scores": a list of objects, each with "dimension" (exact rubric name), '
    '"score" (number within the rubric scale), and "evidence_refs" (object '
    'with "claim_ids", "evidence_ids", "turn_ids": arrays of integer ids '
    "taken ONLY from the session data below). Every score must cite at "
    "least the turns it is based on; never invent ids. A low score on an "
    "empty or vague session still cites the turns that show the vagueness. "
    "Return ONLY valid JSON, no markdown."
)


def _session_block(
    rubric: Rubric, session: Session, turns: list[Turn], claims: list[Claim]
) -> str:
    lines = [
        f"Rubric version {rubric.version}, scale "
        f"{rubric.scale_min}-{rubric.scale_max}. Dimensions:",
    ]
    for dim in rubric.dimensions:
        lines.append(
            f"- {dim.name}: {dim.description} "
            f"LOW {dim.low} MEDIUM {dim.medium} HIGH {dim.high}"
        )
    lines.append("Transcript:")
    for turn in turns:
        who = "Miki" if turn.speaker.value == "miki" else "Candidate"
        lines.append(f"- turn_id={turn.id} {who}: {turn.text[:400]}")
    if claims:
        lines.append("Claims and evidence:")
        for claim in claims:
            lines.append(
                f"- claim_id={claim.id} turn_id={claim.turn_id} "
                f"[{claim.category} conf={claim.confidence:.2f}] "
                f"{claim.claim_text[:200]}"
            )
            for ev in claim.evidence_items:
                lines.append(
                    f"  - evidence_id={ev.id} turn_id={ev.turn_id} "
                    f"({ev.evidence_type.value}) {ev.evidence_text[:160]}"
                )
    else:
        lines.append("Claims and evidence: (none extracted)")
    return "\n".join(lines)


def evaluate_session(
    db: DbSession, session: Session, rubric: Rubric
) -> list[Evaluation]:
    """Score one session on every rubric dimension; persist one row each."""
    turns = (
        db.query(Turn)
        .filter(Turn.session_id == session.id)
        .order_by(Turn.turn_index)
        .all()
    )
    claims = (
        db.query(Claim).filter(Claim.session_id == session.id).order_by(Claim.id).all()
    )
    if not turns:
        raise ValueError(f"Session {session.id} has no turns to evaluate")

    result = call_llm(
        task_type="evaluation",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _session_block(rubric, session, turns, claims)},
        ],
        response_format={"type": "json_object"},
    )
    parsed = result["parsed_json"]
    if not isinstance(parsed, dict) or not isinstance(parsed.get("scores"), list):
        raise ValueError(f"Evaluator did not return a scores list: {parsed!r}")

    valid_claims = {c.id for c in claims}
    valid_evidence = {e.id for c in claims for e in c.evidence_items}
    valid_turns = {t.id for t in turns}
    wanted = {d.name for d in rubric.dimensions}
    rows: list[Evaluation] = []

    for item in parsed["scores"]:
        dim = item.get("dimension")
        if dim not in wanted:
            raise ValueError(f"Unknown dimension {dim!r}, want one of {sorted(wanted)}")
        try:
            score = float(item.get("score"))
        except (TypeError, ValueError):
            raise ValueError(f"Non-numeric score for {dim!r}: {item!r}") from None
        if not rubric.scale_min <= score <= rubric.scale_max:
            raise ValueError(f"Score {score} for {dim!r} outside scale, got {item!r}")
        refs = item.get("evidence_refs") or {}
        for key, valid in (
            ("claim_ids", valid_claims),
            ("evidence_ids", valid_evidence),
            ("turn_ids", valid_turns),
        ):
            ids = refs.get(key, [])
            if not isinstance(ids, list) or any(
                not isinstance(i, int) or i not in valid for i in ids
            ):
                raise ValueError(f"Bad {key} for {dim!r}: {ids!r} (not session ids)")
        rows.append(
            Evaluation(
                session_id=session.id,
                dimension=dim,
                score=score,
                evidence_refs={
                    "claim_ids": refs.get("claim_ids", []),
                    "evidence_ids": refs.get("evidence_ids", []),
                    "turn_ids": refs.get("turn_ids", []),
                },
                rubric_version=rubric.version,
                model_id=result["model_id"],
            )
        )
    if {r.dimension for r in rows} != wanted:
        raise ValueError(f"Missing dimensions: {[r.dimension for r in rows]}")

    db.add_all(rows)
    db.commit()
    logger.info("session %d evaluated on %d dimensions", session.id, len(rows))
    return rows


def evaluate_if_unscored(
    db: DbSession, session: Session, rubric: Rubric
) -> list[Evaluation]:
    """Evaluate once; return existing rows if the session already has them."""
    existing = db.query(Evaluation).filter(Evaluation.session_id == session.id).all()
    if existing:
        return existing
    return evaluate_session(db, session, rubric)


def ref_details(db: DbSession, row: Evaluation) -> dict[str, Any]:
    """Resolve an evaluation's refs to short previews (for the report)."""
    refs: dict[str, Any] = row.evidence_refs or {}
    out: dict[str, Any] = {"claims": [], "evidence": [], "turns": []}
    for cid in refs.get("claim_ids", []):
        claim = db.query(Claim).filter(Claim.id == cid).first()
        if claim:
            out["claims"].append({"id": cid, "text": claim.claim_text[:160]})
    for eid in refs.get("evidence_ids", []):
        ev = db.query(Evidence).filter(Evidence.id == eid).first()
        if ev:
            out["evidence"].append({"id": eid, "text": ev.evidence_text[:160]})
    for tid in refs.get("turn_ids", []):
        turn = db.query(Turn).filter(Turn.id == tid).first()
        if turn:
            out["turns"].append({"id": tid, "text": turn.text[:160]})
    return out
