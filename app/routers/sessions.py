"""Session endpoints: start + answer the text interview loop (Phase 9) + history."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.database import SessionLocal
from app.evaluation import build_report, evaluate_if_unscored, get_normal_rubric
from app.extraction import persist_answer_claims
from app.interview import (
    InterviewState,
    answer_session,
    apply_proposal,
    full_context,
    load_machine,
    recent_claims_for_session,
    recent_turn_texts,
    resolve_target_claim,
    start_session,
)
from app.interview.questions import generate_question_stream, persist_miki_turn
from app.models import CandidateProfile, Evaluation, RoleProfile, Session, User
from app.models.enums import SessionStatus
from app.policy import get_normal_policy
from app.policy.loader import InterviewPolicy

router = APIRouter(tags=["sessions"])


def get_db():
    """Per-request DB session (closed after the request)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Db = Annotated[DbSession, Depends(get_db)]
Policy = Annotated[InterviewPolicy, Depends(get_normal_policy)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]


class StartRequest(BaseModel):
    candidate_profile_id: int
    role_profile_id: int
    mode: str = "normal"


class StartResponse(BaseModel):
    session_id: int
    state: str
    question: str
    policy_version: str


class AnswerRequest(BaseModel):
    text: str


class AnswerResponse(BaseModel):
    question: str
    state: str
    finished: bool
    transition_applied: bool
    claims_found: int
    analysis_ms: int | None = None
    question_ms: int | None = None


class SessionDetail(BaseModel):
    session_id: int
    state: str
    status: str
    turns: int
    claims: int
    policy_version: str
    engine_version: str
    started_at: datetime
    ended_at: datetime | None
    duration_s: int | None


class HistoryDimension(BaseModel):
    dimension: str
    score: float


class HistoryEntry(BaseModel):
    session_id: int
    started_at: datetime
    ended_at: datetime | None
    duration_s: int | None
    status: str
    mode: str
    overall_score: float | None
    dimensions: list[HistoryDimension]


class HistoryResponse(BaseModel):
    sessions: list[HistoryEntry]


def _get_session(db: DbSession, session_id: int, user: User | None = None) -> Session:
    session = db.query(Session).filter(Session.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail=f"No session {session_id}")
    _check_ownership(session, user)
    return session


def _check_ownership(session: Session, user: User | None) -> None:
    """403 when a signed-in user touches another user's session.

    Guest sessions (``user_id`` NULL) stay world-readable by id in V1 —
    the same behavior as before auth existed. Owned sessions are private.
    """
    if user is not None and session.user_id is not None:
        if session.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not your session")


def _format_history_entry(db: DbSession, session: Session) -> HistoryEntry:
    rows = (
        db.query(Evaluation)
        .filter(Evaluation.session_id == session.id)
        .order_by(Evaluation.dimension)
        .all()
    )
    dims = [HistoryDimension(dimension=r.dimension, score=r.score) for r in rows]
    overall = sum(r.score for r in rows) / len(rows) if rows else None
    duration = None
    if session.ended_at is not None:
        duration = int((session.ended_at - session.started_at).total_seconds())
    return HistoryEntry(
        session_id=session.id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_s=duration,
        status=session.status.value,
        mode=session.mode,
        overall_score=overall,
        dimensions=dims,
    )


@router.post("/session/start", response_model=StartResponse, status_code=201)
def start_interview(
    payload: StartRequest, db: Db, policy: Policy, user: OptionalUser
) -> StartResponse:
    """Start an interview; stamps the owner when signed in, guest otherwise."""
    if payload.mode != policy.mode:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown mode {payload.mode!r} (only {policy.mode!r} in V1)",
        )
    cand = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.id == payload.candidate_profile_id)
        .first()
    )
    if cand is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    role = (
        db.query(RoleProfile).filter(RoleProfile.id == payload.role_profile_id).first()
    )
    if role is None:
        raise HTTPException(status_code=404, detail="Role profile not found")
    try:
        session, first_turn = start_session(
            db,
            candidate_profile_id=cand.id,
            role_profile_id=role.id,
            policy=policy,
            user_id=user.id if user else None,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not start: {e}") from e
    return StartResponse(
        session_id=session.id,
        state=InterviewState.OPENING.value,
        question=first_turn.text,
        policy_version=session.policy_version,
    )


@router.post("/session/{session_id}/answer", response_model=AnswerResponse)
def answer(
    payload: AnswerRequest,
    session_id: int,
    db: Db,
    policy: Policy,
    user: OptionalUser,
) -> Any:
    """Submit an answer; runs extraction -> proposal -> validation -> question."""
    session = _get_session(db, session_id, user)
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409, detail=f"Session is {session.status.value}"
        )
    if not (payload.text or "").strip():
        raise HTTPException(status_code=400, detail="Answer text must be non-empty")
    try:
        result = answer_session(db, session, policy, payload.text)
    except ValueError as e:
        msg = str(e)
        if "Malformed LLM response" in msg or "Extraction failed" in msg:
            raise HTTPException(status_code=422, detail=msg) from e
        raise HTTPException(status_code=502, detail=f"LLM step failed: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM step failed: {e}") from e
    return AnswerResponse(**result)


@router.post("/session/{session_id}/answer/stream")
def answer_stream(
    payload: AnswerRequest,
    session_id: int,
    db: Db,
    policy: Policy,
    user: OptionalUser,
) -> StreamingResponse:
    """Stream the next question token-by-token (SSE).

    Same engine as ``/answer`` (merged analysis -> validate -> question),
    but the question streams as ``data: {"delta": ...}`` events so the UI
    renders words instead of waiting. Event flow:
    ``started`` (state/claims/timings) -> ``delta``* -> ``done`` (full text
    already persisted as the miki turn). On failure mid-stream the client
    falls back to ``/answer``; use that endpoint if SSE is unavailable.
    """
    session = _get_session(db, session_id, user)
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409, detail=f"Session is {session.status.value}"
        )
    if not (payload.text or "").strip():
        raise HTTPException(status_code=400, detail="Answer text must be non-empty")

    def _events():
        from app.interview.loop import append_candidate_turn

        def _send(obj: dict[str, Any]) -> str:
            return f"data: {json.dumps(obj)}\n\n"

        try:
            machine = load_machine(db, session.id, policy)
            turn = append_candidate_turn(
                db, session_id=session.id, text=payload.text
            )
            db.refresh(session)
            resume_claims = (session.candidate_profile.extracted_json or {}).get(
                "claims", []
            )
            ctx = full_context(db, session, policy)
            recent = recent_claims_for_session(db, session.id)
            history = [
                t if len(t) <= 600 else t[:600] + "…"
                for t in recent_turn_texts(db, session.id)
            ]
            t0 = time.monotonic()
            try:
                from app.interview.turn_analysis import analyze_turn_robust

                parsed, model_id, _fallback = analyze_turn_robust(
                    turn.text,
                    machine.current_state,
                    policy,
                    recent_claims=recent,
                    coverage=ctx,
                    recent_turns=history,
                    resume_claims=resume_claims
                    if isinstance(resume_claims, list)
                    else [],
                )
            except ValueError as e:
                msg = str(e)
                if "Malformed LLM response" in msg or "Extraction failed" in msg:
                    raise HTTPException(status_code=422, detail=msg) from e
                raise HTTPException(status_code=502, detail=f"LLM step failed: {e}") from e
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"LLM step failed: {e}") from e
            analysis_ms = int((time.monotonic() - t0) * 1000)
            claims = persist_answer_claims(
                db, session_id=session.id, turn_id=turn.id, parsed=parsed
            )
            db.refresh(session)
            applied = apply_proposal(machine, parsed, model_id, ctx)

            closing = machine.current_state == InterviewState.CLOSING and applied
            if closing:
                session.status = SessionStatus.COMPLETED
                session.ended_at = datetime.now(UTC)
                db.commit()
                target = None
            else:
                target = resolve_target_claim(db, session.id, parsed)
            yield _send(
                {
                    "type": "started",
                    "state": machine.current_state.value,
                    "finished": closing,
                    "transition_applied": applied,
                    "claims_found": len(claims),
                    "analysis_ms": analysis_ms,
                }
            )
            t1 = time.monotonic()
            parts: list[str] = []
            try:
                stream = generate_question_stream(
                    machine.current_state,
                    policy,
                    session.candidate_profile.extracted_json or {},
                    session.role_profile.extracted_json or {},
                    target_claim=target,
                    recent_turns=recent_turn_texts(db, session.id),
                )
                for delta in stream:
                    parts.append(delta)
                    yield _send({"type": "delta", "delta": delta})
            except Exception as e:
                raise HTTPException(
                    status_code=502, detail=f"Question stream failed: {e}"
                ) from e
            question = "".join(parts).strip()
            if not question:
                raise HTTPException(status_code=502, detail="Streamed question is empty")
            persist_miki_turn(db, session_id=session.id, text=question)
            yield _send(
                {
                    "type": "done",
                    "question": question,
                    "state": machine.current_state.value,
                    "finished": closing,
                    "transition_applied": applied,
                    "claims_found": len(claims),
                    "analysis_ms": analysis_ms,
                    "question_ms": int((time.monotonic() - t1) * 1000),
                }
            )
        except HTTPException as e:
            yield _send({"type": "error", "status": e.status_code, "detail": e.detail})
        except Exception as e:
            yield _send({"type": "error", "status": 502, "detail": str(e)[:300]})

    return StreamingResponse(_events(), media_type="text/event-stream")


@router.post("/session/{session_id}/abort")
def abort_session(session_id: int, db: Db, user: OptionalUser) -> dict[str, Any]:
    """End an in-progress session early (End Session button); marks ABORTED."""
    session = _get_session(db, session_id, user)
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409, detail=f"Session is {session.status.value}"
        )
    session.status = SessionStatus.ABORTED
    session.ended_at = datetime.now(UTC)
    db.commit()
    return {"session_id": session.id, "status": session.status.value}


@router.get("/sessions/history", response_model=HistoryResponse)
def session_history(
    db: Db,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> HistoryResponse:
    """List past sessions owned by the authenticated user, newest first."""
    sessions = (
        db.query(Session)
        .filter(Session.user_id == user.id)
        .order_by(Session.started_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return HistoryResponse(sessions=[_format_history_entry(db, s) for s in sessions])


@router.get("/session/{session_id}", response_model=SessionDetail)
def session_detail(
    session_id: int, db: Db, policy: Policy, user: OptionalUser
) -> SessionDetail:
    """Inspect a session: derived state, status, turn/claim counts."""
    session = _get_session(db, session_id, user)
    machine = load_machine(db, session.id, policy)
    duration = None
    if session.ended_at is not None:
        duration = int((session.ended_at - session.started_at).total_seconds())
    return SessionDetail(
        session_id=session.id,
        state=machine.current_state.value,
        status=session.status.value,
        turns=len(session.turns),
        claims=len(session.claims),
        policy_version=session.policy_version,
        engine_version=session.engine_version,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_s=duration,
    )


@router.get("/session/{session_id}/report")
def session_report(session_id: int, db: Db, user: OptionalUser) -> dict[str, Any]:
    """Post-interview report: scores with cited evidence + coach summary."""
    session = _get_session(db, session_id, user)
    if session.status != SessionStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Report needs a completed session")
    rubric = get_normal_rubric()
    try:
        evaluate_if_unscored(db, session, rubric)
        return build_report(db, session, rubric)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Report failed: {e}") from e
