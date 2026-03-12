"""Paper Pydantic schemas for request/response validation."""

from datetime import datetime
from pydantic import BaseModel, Field


class PaperUpdate(BaseModel):
    """Schema for updating paper metadata."""

    title: str | None = Field(None, min_length=1, max_length=500)
    authors: list[str] | None = None
    abstract: str | None = None
    year: int | None = Field(None, ge=1900, le=2100)
    journal: str | None = Field(None, max_length=255)
    doi: str | None = Field(None, max_length=255)
    tags: list[str] | None = None


class PaperResponse(BaseModel):
    """Schema for paper data in responses."""

    id: str
    title: str
    authors: list[str] | None
    abstract: str | None
    file_name: str
    file_size: int
    mime_type: str
    workspace_id: str
    uploaded_by: str
    year: int | None
    journal: str | None
    doi: str | None
    tags: list[str] | None
    is_processed: bool
    processing_status: str
    processing_error: str | None
    created_at: datetime
    updated_at: datetime
    chunk_count: int = 0

    model_config = {"from_attributes": True}


class PaperStatusResponse(BaseModel):
    """Schema for paper processing status."""

    id: str
    processing_status: str
    processing_error: str | None
    is_processed: bool


class PaperChunkResponse(BaseModel):
    """Schema for paper chunk data."""

    id: str
    paper_id: str
    chunk_index: int
    content: str

    model_config = {"from_attributes": True}


class PaperUploadResponse(BaseModel):
    """Schema for paper upload confirmation."""

    id: str
    file_name: str
    processing_status: str
    message: str = "Paper uploaded successfully. Processing started."
