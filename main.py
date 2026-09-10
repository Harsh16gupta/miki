"""Miki FastAPI application entrypoint.

Run locally with: ``venv/bin/uvicorn main:app --reload``.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers.auth import router as auth_router
from app.routers.profiles import router as profiles_router
from app.routers.sessions import router as sessions_router
from app.routers.voice import router as voice_router

ROOT = Path(__file__).resolve().parent
# Production build output (``npm run build`` in frontend/) takes precedence;
# legacy ``app/static/index.html`` remains as a fallback until removed.
FRONTEND_DIST = ROOT / "frontend" / "dist"
LEGACY_STATIC = ROOT / "app" / "static"
STATIC_DIR = FRONTEND_DIST if (FRONTEND_DIST / "index.html").exists() else LEGACY_STATIC

app = FastAPI()
# Split-domain prod (Vite :5173 -> API :8000). Dev also works via Vite proxy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(sessions_router)
app.include_router(voice_router)
app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")


@app.middleware("http")
async def spa_fallback(request: Request, call_next):
    """Serve the SPA for extensionless /ui/* deep links (BrowserRouter).

    StaticFiles(html=True) only falls back to index.html at the mount root,
    so /ui/history etc. 404 without this. Real files (with an extension)
    keep their 404 so missing assets never masquerade as the app shell.
    """
    response = await call_next(request)
    path = request.url.path
    if (
        response.status_code == 404
        and path.startswith("/ui")
        and "." not in path.rsplit("/", 1)[-1]
    ):
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index), media_type="text/html")
    return response


@app.get("/")
def root():
    """Landing probe: points manual testers at the real endpoints."""
    return {
        "service": "miki",
        "ui": "/ui",
        "health": "/health",
        "docs": "/docs",
        "endpoints": [
            "POST /auth/register",
            "POST /auth/login",
            "GET /auth/me",
            "POST /candidate-profile",
            "POST /candidate-profile/upload",
            "POST /role-profile",
            "POST /role-profile/upload",
            "POST /session/start",
            "POST /session/{id}/answer",
            "POST /session/{id}/abort",
            "GET /sessions/history",
            "GET /session/{id}",
            "GET /session/{id}/report",
            "WS /session/{id}/voice",
        ],
    }


@app.get("/health")
def health_check():
    """Liveness probe. Returns 200 with ``{"status": "ok"}`` when the API is up."""
    return {"status": "ok"}
