"""Post-interview report builder (Phase 13).

Deterministic composition over evaluation rows (scores + cited evidence
previews) plus one cheap LLM call for plain-language strengths, weaknesses,
hard-to-defend claims, and study topics. JSON API response for V1.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.evaluation.evaluator import ref_details
from app.evaluation.rubric import Rubric
from app.llm.router import call_llm
from app.models import Claim, Evaluation, Session

SUMMARY_PROMPT = (
    "You are a candid interview coach. Given per-dimension scores (1-5) "
    "with the cited evidence, write a single JSON object with keys: "
    '"strengths" (list of 2-4 specific strings naming what went well, '
    "grounded in the cited evidence), "
    '"weaknesses" (list of 2-4 specific strings naming what went poorly), '
    '"hard_to_defend_claims" (list of claim texts from the session that '
    "collapsed or lacked measurement), "
    '"study_topics" (list of 2-4 concrete topics to study next, derived '
    "from the weaknesses). Be specific and blunt, never generic. "
    "Return ONLY valid JSON, no markdown."
)


def summarize_session(
    dimensions: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """One cheap LLM call turning scores into coach prose."""
    result = call_llm(
        task_type="report",
        messages=[
            {"role": "system", "content": SUMMARY_PROMPT},
            {
                "role": "user",
                "content": "Scores with cited evidence:\n"
                + "\n".join(
                    f"- {d['dimension']}: {d['score']} "
                    f"(claims={d['refs']['claims']}, "
                    f"evidence={d['refs']['evidence']})"
                    for d in dimensions
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    parsed = result["parsed_json"]
    if not isinstance(parsed, dict):
        raise ValueError(f"Report summary is not an object: {parsed!r}")
    out: dict[str, list[str]] = {}
    for key in ("strengths", "weaknesses", "hard_to_defend_claims", "study_topics"):
        items = parsed.get(key, [])
        if not isinstance(items, list) or not all(isinstance(s, str) for s in items):
            raise ValueError(f"Report key {key!r} is not a string list: {items!r}")
        out[key] = items
    return out


def build_report(db: DbSession, session: Session, rubric: Rubric) -> dict[str, Any]:
    """Compose the full report dict for a scored session."""
    rows = (
        db.query(Evaluation)
        .filter(Evaluation.session_id == session.id)
        .order_by(Evaluation.dimension)
        .all()
    )
    if not rows:
        raise ValueError(f"Session {session.id} has no evaluations yet")
    dimensions = []
    for row in rows:
        refs = ref_details(db, row)
        dimensions.append(
            {
                "dimension": row.dimension,
                "score": row.score,
                "rubric_version": row.rubric_version,
                "refs": refs,
            }
        )
    claims = db.query(Claim).filter(Claim.session_id == session.id).all()
    summary = summarize_session(dimensions)
    return {
        "session_id": session.id,
        "status": session.status.value,
        "policy_version": session.policy_version,
        "engine_version": session.engine_version,
        "rubric_version": rubric.version,
        "dimensions": dimensions,
        "claims_examined": len(claims),
        **summary,
    }
