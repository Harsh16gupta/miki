"""Miki FastAPI application entrypoint.

Run locally with: ``venv/bin/uvicorn main:app --reload``.
Interview, session, and voice endpoints are added in later phases; this module
currently exposes only the health check from Phase 0.
"""

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    """Liveness probe. Returns 200 with ``{"status": "ok"}`` when the API is up."""
    return {"status": "ok"}
