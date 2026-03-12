"""Workspace Pydantic schemas for request/response validation."""

from datetime import datetime
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    """Schema for creating a workspace."""

    name: str = Field(..., min_length=1, max_length=255, description="Workspace name")
    description: str | None = Field(
        None, max_length=1000, description="Workspace description"
    )
    color: str = Field(
        "#3b82f6", pattern=r"^#[0-9a-fA-F]{6}$", description="Hex color code"
    )


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")


class WorkspaceResponse(BaseModel):
    """Schema for workspace data in responses."""

    id: str
    name: str
    description: str | None
    color: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    paper_count: int = 0
    conversation_count: int = 0

    model_config = {"from_attributes": True}


class WorkspaceStats(BaseModel):
    """Schema for workspace statistics."""

    paper_count: int
    conversation_count: int
    last_activity: datetime | None
