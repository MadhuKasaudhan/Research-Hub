"""Authentication router: register, login, refresh, and profile endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.common import TokenResponse
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    UserWithToken,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_user_by_email,
    hash_password,
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Request body helpers
# ---------------------------------------------------------------------------


class RefreshTokenRequest(BaseModel):
    """Body for the ``POST /refresh`` endpoint."""

    refresh_token: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_tokens(user: User) -> dict[str, str]:
    """Return a dict with ``access_token`` and ``refresh_token`` for *user*."""
    token_data = {"sub": user.id, "email": user.email}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=UserWithToken,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserWithToken:
    """Create a new user account and return an access/refresh token pair."""
    existing = await get_user_by_email(db, user_data.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    user = await create_user(db, user_data)
    tokens = _build_tokens(user)

    return UserWithToken(
        user=UserResponse.model_validate(user),
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain tokens",
)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user with email/password and return a token pair."""
    user = await authenticate_user(db, credentials.email, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = _build_tokens(user)

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh an access token",
)
async def refresh(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access/refresh token pair."""
    token_data = decode_token(body.refresh_token)

    user = await get_user_by_email(db, token_data.email)  # type: ignore[arg-type]
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = _build_tokens(user)

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current user's profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update the current user's profile",
)
async def update_me(
    updates: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update the authenticated user's name and/or password."""
    if updates.full_name is None and updates.password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update were provided",
        )

    if updates.full_name is not None:
        current_user.full_name = updates.full_name

    if updates.password is not None:
        current_user.hashed_password = hash_password(updates.password)

    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)
