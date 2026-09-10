"""Profile routers package (Phase 3)."""

from app.routers.profiles import router as profiles_router
from app.routers.sessions import router as sessions_router
from app.routers.voice import router as voice_router

__all__ = ["profiles_router", "sessions_router", "voice_router"]
