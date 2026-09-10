"""Claim/evidence extraction for one candidate answer (Phase 6).

Runs after every candidate turn: the LLM pulls verifiable claims, a topic
category, a confidence signal, and supporting/contradicting/vague evidence
out of the answer (using recent turns + resume claims as context), then the
rows are persisted to ``claim``/``evidence`` linked to the source turn.
Uses ``task_type="extraction"`` (cheap model), traced as ``llm:extraction``.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.llm.router import call_llm
from app.models import Claim, Evidence
from app.models.enums import EvidenceType

SYSTEM_PROMPT = (
    "You are a claim extractor for an interview training system. "
    "Given the candidate's latest answer plus recent conversation context "
    "and the resume claims, extract a single JSON object with one key "
    '"claims": a list of objects, each with: '
    '"claim_text" (the assertion as one standalone sentence), '
    '"category" (short topic bucket, e.g. performance, system_design, '
    "communication, ownership), "
    '"confidence" (0.0-1.0: how strongly the answer substantiates it; '
    "use 0.3 or lower for vague hand-waving with no specifics, and mark "
    "such evidence vague, never supports), "
    '"contradicts_earlier" (true if it conflicts with an earlier turn '
    "or a resume claim, else false), "
    '"evidence": a list of objects with "evidence_text" (the exact quote '
    "or paraphrase from the answer) and "
    '"evidence_type" (one of supports, contradicts, vague). '
    "A vague answer with no verifiable content yields an empty claims list. "
    "Return ONLY valid JSON, no markdown."
)

_VALID_EVIDENCE_TYPES = {"supports", "contradicts", "vague"}


def _context_block(recent_turns: list[str], resume_claims: list[str]) -> str:
    parts = []
    if recent_turns:
        lines = "\n".join(f"- {t}" for t in recent_turns)
        parts.append("Recent conversation:\n" + lines)
    else:
        parts.append("Recent conversation: (none yet)")
    if resume_claims:
        parts.append("Resume claims:\n" + "\n".join(f"- {c}" for c in resume_claims))
    else:
        parts.append("Resume claims: (none)")
    return "\n".join(parts)


def extract_answer_claims(
    answer_text: str,
    recent_turns: list[str] | None = None,
    resume_claims: list[str] | None = None,
) -> dict[str, Any]:
    """Extract ``{"claims": [...]}`` from one candidate answer."""
    if not answer_text or not answer_text.strip():
        raise ValueError("Cannot extract claims from empty answer")
    user_content = (
        f"{_context_block(recent_turns or [], resume_claims or [])}\n\n"
        f"Latest answer:\n{answer_text}"
    )
    result = call_llm(
        task_type="extraction",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
    )
    parsed = result["parsed_json"]
    if not isinstance(parsed, dict) or not isinstance(parsed.get("claims"), list):
        raise ValueError(f"Extraction did not return a claims list: {parsed!r}")
    return parsed


def persist_answer_claims(
    db: DbSession, *, session_id: int, turn_id: int, parsed: dict[str, Any]
) -> list[Claim]:
    """Write parsed claims + evidence rows linked to the source turn."""
    created: list[Claim] = []
    for item in parsed.get("claims", []):
        if not isinstance(item, dict) or not str(item.get("claim_text", "")).strip():
            continue
        try:
            confidence = float(item.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        claim = Claim(
            session_id=session_id,
            turn_id=turn_id,
            claim_text=str(item["claim_text"]).strip(),
            category=str(item.get("category", "general")).strip() or "general",
            confidence=min(1.0, max(0.0, confidence)),
        )
        db.add(claim)
        db.flush()  # assign claim.id for the evidence rows below
        for ev in item.get("evidence", []):
            if not isinstance(ev, dict):
                continue
            ev_type = str(ev.get("evidence_type", "vague")).strip().lower()
            if ev_type not in _VALID_EVIDENCE_TYPES:
                raise ValueError(f"Unknown evidence_type: {ev_type!r}")
            ev_text = str(ev.get("evidence_text", "")).strip()
            if not ev_text:
                continue
            db.add(
                Evidence(
                    claim_id=claim.id,
                    turn_id=turn_id,
                    evidence_text=ev_text,
                    evidence_type=EvidenceType(ev_type),
                )
            )
        created.append(claim)
    db.commit()
    return created
