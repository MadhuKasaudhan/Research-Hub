"""Service for managing conversations and message history."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole

logger = logging.getLogger(__name__)


async def get_conversation_history(
    conversation_id: str,
    db: AsyncSession,
    limit: int = 20,
) -> list[dict[str, str]]:
    """Get conversation history formatted for Groq API.

    Returns list of {role, content} dicts for the last `limit` messages.
    """
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()

    # Reverse to get chronological order
    messages = list(reversed(messages))

    history: list[dict[str, str]] = []
    for msg in messages:
        history.append(
            {
                "role": msg.role.value
                if isinstance(msg.role, MessageRole)
                else msg.role,
                "content": msg.content,
            }
        )

    return history


async def save_message(
    conversation_id: str,
    role: MessageRole,
    content: str,
    db: AsyncSession,
    msg_metadata: dict | None = None,
    tokens_used: int | None = None,
) -> Message:
    """Save a message to a conversation."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        msg_metadata=msg_metadata,
        tokens_used=tokens_used,
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)
    logger.info(
        "[AGENT] Saved %s message to conversation %s", role.value, conversation_id
    )
    return message


async def get_conversation_message_count(
    conversation_id: str,
    db: AsyncSession,
) -> int:
    """Get the number of messages in a conversation."""
    result = await db.execute(
        select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
    )
    return result.scalar() or 0
