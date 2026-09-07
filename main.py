"""Miki FastAPI application entrypoint.

Run locally with: ``venv/bin/uvicorn main:app --reload``.
"""

from fastapi import FastAPI

from app.routers.profiles import router as profiles_router
from app.routers.sessions import router as sessions_router
from app.routers.voice import router as voice_router

app = FastAPI()
app.include_router(profiles_router)
app.include_router(sessions_router)
app.include_router(voice_router)


@app.get("/")
def root():
    """Landing probe: points manual testers at the real endpoints."""
    return {
        "service": "miki",
        "health": "/health",
        "docs": "/docs",
        "endpoints": [
            "POST /candidate-profile",
            "POST /candidate-profile/upload",
            "POST /role-profile",
            "POST /role-profile/upload",
            "POST /session/start",
            "POST /session/{id}/answer",
            "GET /session/{id}",
            "GET /session/{id}/report",
            "WS /session/{id}/voice",
        ],
    }


@app.get("/health")
def health_check():
    """Liveness probe. Returns 200 with ``{"status": "ok"}`` when the API is up."""
    return {"status": "ok"}
