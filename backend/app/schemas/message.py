"""Message Pydantic schemas for request/response validation."""

from datetime import datetime
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for sending a chat message."""

    content: str = Field(
        ..., min_length=1, max_length=10000, description="Message content"
    )
    paper_ids: list[str] | None = Field(
        None, description="Optional paper IDs to focus context on"
    )


class MessageResponse(BaseModel):
    """Schema for message data in responses."""

    id: str
    conversation_id: str
    role: str
    content: str
    metadata: dict | None = Field(None, validation_alias="msg_metadata")
    tokens_used: int | None
    created_at: datetime
    sources: list[str] | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ChatResponse(BaseModel):
    """Schema for chat API response with AI answer."""

    message_id: str
    content: str
    sources: list[str]
    tokens_used: int


class AnalysisRequest(BaseModel):
    """Schema for paper analysis request."""

    analysis_type: str = Field(
        ...,
        description="Type of analysis: summary, key_findings, methodology, critique, concepts",
    )


class AnalysisResponse(BaseModel):
    """Schema for analysis result."""

    result: str
    analysis_type: str
    tokens_used: int


class SynthesisRequest(BaseModel):
    """Schema for cross-paper synthesis request."""

    paper_ids: list[str] = Field(..., min_length=2, description="At least 2 paper IDs")
    synthesis_type: str = Field(
        ..., description="Type of synthesis: compare, themes, timeline, gaps"
    )


class SynthesisResponse(BaseModel):
    """Schema for synthesis result."""

    result: str
    synthesis_type: str
    papers_used: list[str]
    tokens_used: int
