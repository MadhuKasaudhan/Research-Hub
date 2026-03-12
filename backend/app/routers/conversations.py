"""Conversations router for creating, listing, and managing chat conversations."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.user import User
from app.models.workspace import Workspace
from app.routers.workspaces import verify_workspace_ownership
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.schemas.message import MessageResponse
from app.utils.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Conversations"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _verify_conversation_access(
    conversation_id: str,
    user_id: str,
    db: AsyncSession,
) -> Conversation:
    """Verify that a conversation exists and the user owns its parent workspace.

    Returns:
        The Conversation instance if access is confirmed.

    Raises:
        HTTPException: 404 if conversation not found, 403 if not the owner.
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Verify workspace ownership
    ws_result = await db.execute(
        select(Workspace).where(Workspace.id == conversation.workspace_id)
    )
    workspace = ws_result.scalar_one_or_none()

    if workspace is None or workspace.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation",
        )

    return conversation


async def _get_message_count(conversation_id: str, db: AsyncSession) -> int:
    """Return the total number of messages in a conversation."""
    result = await db.execute(
        select(func.count())
        .select_from(Message)
        .where(Message.conversation_id == conversation_id)
    )
    return result.scalar_one()


async def _get_last_message_preview(
    conversation_id: str,
    db: AsyncSession,
) -> str | None:
    """Return a preview of the most recent message content (max 100 chars)."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    last_message = result.scalar_one_or_none()
    if last_message is None:
        return None
    preview = last_message.content[:100]
    if len(last_message.content) > 100:
        preview += "..."
    return preview


def _build_conversation_response(
    conversation: Conversation,
    message_count: int = 0,
    last_message_preview: str | None = None,
) -> ConversationResponse:
    """Build a ConversationResponse from a Conversation model instance."""
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        workspace_id=conversation.workspace_id,
        paper_ids=conversation.paper_ids,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=message_count,
        last_message_preview=last_message_preview,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/workspaces/{workspace_id}/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    workspace_id: str,
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ConversationResponse:
    """Create a new conversation in a workspace."""
    await verify_workspace_ownership(workspace_id, current_user.id, db)

    conversation = Conversation(
        title=data.title,
        workspace_id=workspace_id,
        paper_ids=data.paper_ids,
    )
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)

    logger.info(
        "[AGENT] Created conversation '%s' in workspace %s",
        conversation.title,
        workspace_id,
    )

    return _build_conversation_response(conversation, message_count=0)


@router.get(
    "/workspaces/{workspace_id}/conversations",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    workspace_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ConversationResponse]:
    """List conversations in a workspace, sorted by updated_at desc."""
    await verify_workspace_ownership(workspace_id, current_user.id, db)

    offset = (page - 1) * size
    result = await db.execute(
        select(Conversation)
        .where(Conversation.workspace_id == workspace_id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(size)
    )
    conversations = result.scalars().all()

    items: list[ConversationResponse] = []
    for conv in conversations:
        message_count = await _get_message_count(conv.id, db)
        last_preview = await _get_last_message_preview(conv.id, db)
        items.append(_build_conversation_response(conv, message_count, last_preview))

    return items


@router.get(
    "/conversations/{conversation_id}",
    response_model=dict,
)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Get a conversation with its full message history."""
    conversation = await _verify_conversation_access(
        conversation_id, current_user.id, db
    )

    message_count = await _get_message_count(conversation_id, db)
    last_preview = await _get_last_message_preview(conversation_id, db)

    conv_response = _build_conversation_response(
        conversation, message_count, last_preview
    )

    # Fetch all messages ordered chronologically
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = messages_result.scalars().all()

    message_responses: list[MessageResponse] = []
    for msg in messages:
        sources: list[str] | None = None
        if msg.msg_metadata and isinstance(msg.msg_metadata, dict):
            sources = msg.msg_metadata.get("sources")

        message_responses.append(
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role.value if isinstance(msg.role, MessageRole) else msg.role,
                content=msg.content,
                metadata=msg.msg_metadata,
                tokens_used=msg.tokens_used,
                created_at=msg.created_at,
                sources=sources,
            )
        )

    return {
        "conversation": conv_response.model_dump(),
        "messages": [m.model_dump() for m in message_responses],
    }


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a conversation and all its messages."""
    conversation = await _verify_conversation_access(
        conversation_id, current_user.id, db
    )

    await db.delete(conversation)
    await db.flush()

    logger.info("[AGENT] Deleted conversation %s", conversation_id)
