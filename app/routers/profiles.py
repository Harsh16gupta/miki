"""Phase 3 ingestion endpoints: resume and JD upload + LLM extraction.

Each endpoint accepts PDF or plain text via any of:
- JSON: ``{"text": "..."}``
- File: multipart/form-data with ``file`` field (PDF or .txt)
- Raw: text/plain body

Flow: raw text -> LLM extraction -> DB row.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
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


class ProfileResponse(BaseModel):
    id: int
    extracted_json: dict[str, Any]


async def _read_raw_text(request: Request, field_name: str = "text") -> str:
    """Read raw text from JSON, multipart file upload, or plain-text body."""
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid JSON body") from e
        text = (body.get(field_name) or body.get("raw_text") or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="JSON needs non-empty text")
        return text

    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("file")
        if upload is not None:
            try:
                data = await upload.read()  # type: ignore[union-attr]
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Could not read file: {e}"
                ) from e
            if not data:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            try:
                filename = getattr(upload, "filename", None)
                return extract_text_from_bytes(data, filename=filename)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
        text_field = form.get(field_name) or form.get("raw_text")
        if text_field:
            text = str(text_field).strip()
            if text:
                return text
        raise HTTPException(status_code=400, detail="Form needs file or text field")

    try:
        body_bytes = await request.body()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read body: {e}") from e
    if not body_bytes.strip():
        raise HTTPException(status_code=400, detail="Empty body: send JSON or file")
    if body_bytes[:4] == b"%PDF":
        try:
            return extract_text_from_bytes(body_bytes, filename="upload.pdf")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        text = body_bytes.decode("utf-8").strip()
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=415, detail="Unsupported content type") from e
    if not text:
        raise HTTPException(status_code=400, detail="Empty text body")
    return text


@router.post("/candidate-profile", response_model=ProfileResponse, status_code=201)
async def create_candidate_profile(request: Request, db: DbSession) -> ProfileResponse:
    """Upload a resume (PDF or text), return extracted skills/projects/claims."""
    raw_text = await _read_raw_text(request)
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


@router.post("/role-profile", response_model=ProfileResponse, status_code=201)
async def create_role_profile(request: Request, db: DbSession) -> ProfileResponse:
    """Upload a job description (PDF or text), return structured requirements."""
    raw_text = await _read_raw_text(request)
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
