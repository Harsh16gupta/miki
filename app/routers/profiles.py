"""Phase 3 ingestion endpoints: resume and JD upload + LLM extraction.

Two shapes per profile so Swagger UI stays usable:
- ``POST /candidate-profile`` / ``POST /role-profile`` take JSON
  ``{"text": "..."}`` (typed body, editable in docs).
- ``POST /candidate-profile/upload`` / ``POST /role-profile/upload``
  take a multipart ``file`` (PDF or .txt) with a real file-picker button.

Flow: raw text -> LLM extraction -> DB row.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.ingest.extraction import extract_candidate_profile, extract_role_profile
from app.ingest.pdf import extract_text_from_bytes
from app.models import CandidateProfile, RoleProfile

router = APIRouter(tags=["profiles"])


def get_db():
    """Per-request DB session (closed after the request)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


class TextPayload(BaseModel):
    text: str


class ProfileResponse(BaseModel):
    id: int
    extracted_json: dict[str, Any]


def _require_text(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Field 'text' must be non-empty")
    return cleaned


async def _file_to_text(upload: UploadFile) -> str:
    try:
        data = await upload.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}") from e
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    try:
        return extract_text_from_bytes(data, filename=upload.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


def _save_candidate(db: Session, raw_text: str) -> ProfileResponse:
    try:
        extracted = extract_candidate_profile(raw_text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Extraction failed: {e}") from e
    except Exception as e:
        msg = f"LLM extraction failed: {e}"
        raise HTTPException(status_code=502, detail=msg) from e
    row = CandidateProfile(raw_resume_text=raw_text, extracted_json=extracted)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ProfileResponse(id=row.id, extracted_json=row.extracted_json)


def _save_role(db: Session, raw_text: str) -> ProfileResponse:
    try:
        extracted = extract_role_profile(raw_text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Extraction failed: {e}") from e
    except Exception as e:
        msg = f"LLM extraction failed: {e}"
        raise HTTPException(status_code=502, detail=msg) from e
    row = RoleProfile(raw_jd_text=raw_text, extracted_json=extracted)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ProfileResponse(id=row.id, extracted_json=row.extracted_json)


@router.post("/candidate-profile", response_model=ProfileResponse, status_code=201)
def create_candidate_profile(payload: TextPayload, db: DbSession) -> ProfileResponse:
    """Submit a resume as JSON text, return extracted skills/projects/claims."""
    return _save_candidate(db, _require_text(payload.text))


@router.post(
    "/candidate-profile/upload", response_model=ProfileResponse, status_code=201
)
async def upload_candidate_profile(
    db: DbSession, file: Annotated[UploadFile, File(description="Resume PDF or .txt")]
) -> ProfileResponse:
    """Upload a resume file (PDF or .txt), return extracted structure."""
    return _save_candidate(db, await _file_to_text(file))


@router.post("/role-profile", response_model=ProfileResponse, status_code=201)
def create_role_profile(payload: TextPayload, db: DbSession) -> ProfileResponse:
    """Submit a job description as JSON text, return structured requirements."""
    return _save_role(db, _require_text(payload.text))


@router.post("/role-profile/upload", response_model=ProfileResponse, status_code=201)
async def upload_role_profile(
    db: DbSession, file: Annotated[UploadFile, File(description="JD PDF or .txt")]
) -> ProfileResponse:
    """Upload a job-description file (PDF or .txt), return structured requirements."""
    return _save_role(db, await _file_to_text(file))
