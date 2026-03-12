"""ResearchHub AI - Workspaces router for CRUD operations on workspaces."""

import math
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.conversation import Conversation
from app.models.paper import Paper
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.common import PaginatedResponse
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceStats,
    WorkspaceUpdate,
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


async def verify_workspace_ownership(
    workspace_id: str, user_id: str, db: AsyncSession
) -> Workspace:
    """Verify that a workspace exists and belongs to the given user.

    Args:
        workspace_id: The UUID of the workspace.
        user_id: The UUID of the user to verify ownership against.
        db: The async database session.

    Returns:
        The Workspace instance if ownership is confirmed.

    Raises:
        HTTPException: 404 if workspace not found, 403 if not the owner.
    """
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = result.scalar_one_or_none()

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    if workspace.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace",
        )

    return workspace


@router.get("", response_model=PaginatedResponse[WorkspaceResponse])
async def list_workspaces(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[WorkspaceResponse]:
    """List all workspaces owned by the current user with pagination."""
    # Count total workspaces for the user
    count_query = (
        select(func.count())
        .select_from(Workspace)
        .where(Workspace.owner_id == current_user.id)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch workspaces with offset/limit
    offset = (page - 1) * size
    workspaces_query = (
        select(Workspace)
        .where(Workspace.owner_id == current_user.id)
        .order_by(Workspace.updated_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(workspaces_query)
    workspaces = result.scalars().all()

    # Build responses with paper_count and conversation_count per workspace
    items: list[WorkspaceResponse] = []
    for ws in workspaces:
        paper_count_result = await db.execute(
            select(func.count()).select_from(Paper).where(Paper.workspace_id == ws.id)
        )
        paper_count = paper_count_result.scalar_one()

        conversation_count_result = await db.execute(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.workspace_id == ws.id)
        )
        conversation_count = conversation_count_result.scalar_one()

        items.append(
            WorkspaceResponse(
                id=ws.id,
                name=ws.name,
                description=ws.description,
                color=ws.color,
                owner_id=ws.owner_id,
                created_at=ws.created_at,
                updated_at=ws.updated_at,
                paper_count=paper_count,
                conversation_count=conversation_count,
            )
        )

    pages = math.ceil(total / size) if total > 0 else 1

    return PaginatedResponse[WorkspaceResponse](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    data: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkspaceResponse:
    """Create a new workspace for the current user."""
    workspace = Workspace(
        name=data.name,
        description=data.description,
        color=data.color,
        owner_id=current_user.id,
    )
    db.add(workspace)
    await db.flush()
    await db.refresh(workspace)

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        color=workspace.color,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        paper_count=0,
        conversation_count=0,
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkspaceResponse:
    """Get workspace details by ID with paper count."""
    workspace = await verify_workspace_ownership(workspace_id, current_user.id, db)

    paper_count_result = await db.execute(
        select(func.count())
        .select_from(Paper)
        .where(Paper.workspace_id == workspace.id)
    )
    paper_count = paper_count_result.scalar_one()

    conversation_count_result = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.workspace_id == workspace.id)
    )
    conversation_count = conversation_count_result.scalar_one()

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        color=workspace.color,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        paper_count=paper_count,
        conversation_count=conversation_count,
    )


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    data: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkspaceResponse:
    """Update an existing workspace's metadata."""
    workspace = await verify_workspace_ownership(workspace_id, current_user.id, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)

    workspace.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(workspace)

    paper_count_result = await db.execute(
        select(func.count())
        .select_from(Paper)
        .where(Paper.workspace_id == workspace.id)
    )
    paper_count = paper_count_result.scalar_one()

    conversation_count_result = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.workspace_id == workspace.id)
    )
    conversation_count = conversation_count_result.scalar_one()

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        color=workspace.color,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        paper_count=paper_count,
        conversation_count=conversation_count,
    )


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a workspace and all its associated papers and conversations."""
    workspace = await verify_workspace_ownership(workspace_id, current_user.id, db)

    await db.delete(workspace)
    await db.flush()


@router.get("/{workspace_id}/stats", response_model=WorkspaceStats)
async def get_workspace_stats(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkspaceStats:
    """Get statistics for a workspace."""
    workspace = await verify_workspace_ownership(workspace_id, current_user.id, db)

    paper_count_result = await db.execute(
        select(func.count())
        .select_from(Paper)
        .where(Paper.workspace_id == workspace.id)
    )
    paper_count = paper_count_result.scalar_one()

    conversation_count_result = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.workspace_id == workspace.id)
    )
    conversation_count = conversation_count_result.scalar_one()

    # Determine last activity: most recent updated_at across papers and conversations
    last_paper_result = await db.execute(
        select(func.max(Paper.updated_at)).where(Paper.workspace_id == workspace.id)
    )
    last_paper_activity: datetime | None = last_paper_result.scalar_one_or_none()

    last_conversation_result = await db.execute(
        select(func.max(Conversation.updated_at)).where(
            Conversation.workspace_id == workspace.id
        )
    )
    last_conversation_activity: datetime | None = (
        last_conversation_result.scalar_one_or_none()
    )

    last_activity: datetime | None = None
    candidates = [
        ts
        for ts in [
            last_paper_activity,
            last_conversation_activity,
            workspace.updated_at,
        ]
        if ts is not None
    ]
    if candidates:
        last_activity = max(candidates)

    return WorkspaceStats(
        paper_count=paper_count,
        conversation_count=conversation_count,
        last_activity=last_activity,
    )
