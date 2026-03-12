"""Custom exception classes and global FastAPI exception handlers."""

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------


class ResearchHubError(Exception):
    """Base exception for ResearchHub AI."""

    def __init__(self, detail: str, code: str = "INTERNAL_ERROR") -> None:
        self.detail = detail
        self.code = code
        super().__init__(detail)


class NotFoundError(ResearchHubError):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(detail=detail, code="NOT_FOUND")


class ForbiddenError(ResearchHubError):
    """Access denied."""

    def __init__(self, detail: str = "Access denied") -> None:
        super().__init__(detail=detail, code="FORBIDDEN")


class BadRequestError(ResearchHubError):
    """Invalid request data."""

    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(detail=detail, code="BAD_REQUEST")


class ProcessingError(ResearchHubError):
    """Paper processing failure."""

    def __init__(self, detail: str = "Processing failed") -> None:
        super().__init__(detail=detail, code="PROCESSING_ERROR")


class EmbeddingError(ResearchHubError):
    """Vector embedding failure."""

    def __init__(self, detail: str = "Embedding operation failed") -> None:
        super().__init__(detail=detail, code="EMBEDDING_ERROR")


class AuthenticationError(ResearchHubError):
    """Authentication failure."""

    def __init__(self, detail: str = "Authentication failed") -> None:
        super().__init__(detail=detail, code="AUTHENTICATION_ERROR")


class GroqAPIError(ResearchHubError):
    """Groq API call failure."""

    def __init__(self, detail: str = "Groq API call failed") -> None:
        super().__init__(detail=detail, code="GROQ_API_ERROR")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _error_response(status_code: int, detail: str, code: str) -> JSONResponse:
    """Build a consistent JSON error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": detail,
            "code": code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ---------------------------------------------------------------------------
# Status-code mapping for custom exceptions
# ---------------------------------------------------------------------------

_STATUS_MAP: dict[type[ResearchHubError], int] = {
    NotFoundError: 404,
    ForbiddenError: 403,
    BadRequestError: 400,
    AuthenticationError: 401,
    ProcessingError: 422,
    EmbeddingError: 500,
    GroqAPIError: 502,
}


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application."""

    @app.exception_handler(ResearchHubError)
    async def researchhub_error_handler(
        request: Request, exc: ResearchHubError
    ) -> JSONResponse:
        status_code = _STATUS_MAP.get(type(exc), 500)
        return _error_response(status_code, exc.detail, exc.code)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        detail_str: str = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        code = "HTTP_ERROR"
        if exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"
        elif exc.status_code == 404:
            code = "NOT_FOUND"
        elif exc.status_code == 422:
            code = "VALIDATION_ERROR"
        return _error_response(exc.status_code, detail_str, code)

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Log unexpected errors but never leak internal details
        import logging

        logger = logging.getLogger("researchhub")
        logger.exception(
            "Unhandled exception on %s %s", request.method, request.url.path
        )
        return _error_response(
            500,
            "An internal server error occurred",
            "INTERNAL_ERROR",
        )
