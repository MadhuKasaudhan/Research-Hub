"""Conversation Pydantic schemas for request/response validation."""

from datetime import datetime
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""

    title: str = Field("New Conversation", min_length=1, max_length=255)
    paper_ids: list[str] | None = None


class ConversationResponse(BaseModel):
    """Schema for conversation data in responses."""

    id: str
    title: str
    workspace_id: str
    paper_ids: list[str] | None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message_preview: str | None = None

    model_config = {"from_attributes": True}
