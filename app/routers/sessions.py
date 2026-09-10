"""Session endpoints: start + answer the text interview loop (Phase 9) + history."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.database import SessionLocal
from app.evaluation import build_report, evaluate_if_unscored, get_normal_rubric
from app.interview import InterviewState, answer_session, load_machine, start_session
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


class SessionDetail(BaseModel):
    session_id: int
    state: str
    status: str
    turns: int
    claims: int
    policy_version: str
    engine_version: str


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
    return SessionDetail(
        session_id=session.id,
        state=machine.current_state.value,
        status=session.status.value,
        turns=len(session.turns),
        claims=len(session.claims),
        policy_version=session.policy_version,
        engine_version=session.engine_version,
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
