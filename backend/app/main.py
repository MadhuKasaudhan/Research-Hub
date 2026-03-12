"""ResearchHub AI - FastAPI application entry point."""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.schemas.common import HealthResponse
from app.utils.exceptions import register_exception_handlers

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("researchhub")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup / shutdown lifecycle."""
    settings = get_settings()

    logger.info("Starting %s v%s", settings.app_name, settings.app_version)

    # Initialize the database (creates tables if they don't exist)
    await init_db(settings.database_url)
    logger.info("Database initialized: %s", settings.database_url)

    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info("Upload directory ready: %s", settings.upload_dir)

    # Ensure ChromaDB persist directory exists
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    logger.info("ChromaDB directory ready: %s", settings.chroma_persist_dir)

    yield

    logger.info("Shutting down %s", settings.app_name)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent Research Paper Management and Analysis System powered by Agentic AI",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

register_exception_handlers(app)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from app.routers.auth import router as auth_router  # noqa: E402
from app.routers.workspaces import router as workspaces_router  # noqa: E402
from app.routers.papers import router as papers_router  # noqa: E402
from app.routers.conversations import router as conversations_router  # noqa: E402
from app.routers.chat import router as chat_router  # noqa: E402
from app.routers.search import router as search_router  # noqa: E402

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=f"{API_PREFIX}/auth")
app.include_router(workspaces_router, prefix=API_PREFIX)
app.include_router(papers_router, prefix=API_PREFIX)
app.include_router(conversations_router, prefix=API_PREFIX)
app.include_router(chat_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Static file serving (uploaded papers)
# ---------------------------------------------------------------------------

if os.path.isdir(settings.upload_dir):
    app.mount(
        "/uploads",
        StaticFiles(directory=settings.upload_dir),
        name="uploads",
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Return application health status."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
    )
