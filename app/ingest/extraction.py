"""LLM extraction prompts for Phase 3 ingestion.

Both functions go through ``call_llm(task_type="extraction", ...)``
with JSON response format, traceable in Langfuse as ``llm:extraction``.
"""

from __future__ import annotations

from typing import Any

from app.llm.router import call_llm

CANDIDATE_SYSTEM_PROMPT = (
    "You are a resume parser for an interview training system. "
    "Given the raw resume text, extract a single JSON object with keys: "
    '"skills" (list of strings), '
    '"projects" (list of {name, description} objects, 1-2 sentences each), '
    '"claims" (list of explicit probe-worthy claims, e.g. reduced latency). '
    "Return ONLY valid JSON, no markdown. Use empty lists when missing."
)

ROLE_SYSTEM_PROMPT = (
    "You are a job-description parser for an interview training system. "
    "Given the raw JD text, extract a single JSON object with keys: "
    '"required_skills" (list), "preferred_skills" (list), '
    '"responsibilities" (list), '
    '"seniority_signal" (one of senior/mid-level/junior/staff/unknown). '
    "Return ONLY valid JSON, no markdown."
)


def _extract_json(system_prompt: str, raw_text: str) -> dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise ValueError("Cannot extract from empty text")
    result = call_llm(
        task_type="extraction",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text},
        ],
        response_format={"type": "json_object"},
    )
    parsed = result["parsed_json"]
    if not isinstance(parsed, dict):
        raise ValueError(f"Extraction did not return a JSON object: {parsed!r}")
    return parsed


def extract_candidate_profile(raw_resume_text: str) -> dict[str, Any]:
    """Extract skills, projects, and claims from raw resume text."""
    data = _extract_json(CANDIDATE_SYSTEM_PROMPT, raw_resume_text)
    return {
        "skills": data.get("skills", []),
        "projects": data.get("projects", []),
        "claims": data.get("claims", []),
    }


def extract_role_profile(raw_jd_text: str) -> dict[str, Any]:
    """Extract requirements and seniority from raw JD text."""
    data = _extract_json(ROLE_SYSTEM_PROMPT, raw_jd_text)
    return {
        "required_skills": data.get("required_skills", []),
        "preferred_skills": data.get("preferred_skills", []),
        "responsibilities": data.get("responsibilities", []),
        "seniority_signal": data.get("seniority_signal", "unknown"),
    }
