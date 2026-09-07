"""
VoiceShield FastAPI application entry point.

Phase 1 scope: app factory, structured logging, CORS, database
initialization, and a health endpoint. API routers, WebSocket endpoints, and
AI wiring are added in later phases.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.session import init_db
from app.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("voiceshield.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup/shutdown work. Creates DB tables on boot."""
    init_db()
    logger.info("startup complete", extra={"component": "main"})
    yield


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Real-Time Conversational Deepfake Firewall",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST routers
    from app.api.calls import router as calls_router
    from app.api.speakers import router as speakers_router
    from app.websocket.calls import router as ws_router

    app.include_router(speakers_router)
    app.include_router(calls_router)
    app.include_router(ws_router)

    @app.get("/health", tags=["system"])
    def health() -> dict:
        """Liveness probe. Confirms the app and DB config are wired up."""
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
        }

    return app


app = create_app()
