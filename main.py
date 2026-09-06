"""Miki FastAPI application entrypoint.

Run locally with: ``venv/bin/uvicorn main:app --reload``.
"""

from fastapi import FastAPI

from app.routers.profiles import router as profiles_router

app = FastAPI()
app.include_router(profiles_router)


@app.get("/health")
def health_check():
    """Liveness probe. Returns 200 with ``{"status": "ok"}`` when the API is up."""
    return {"status": "ok"}
