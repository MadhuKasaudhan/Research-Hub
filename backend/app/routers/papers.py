"""ResearchHub AI - Papers router for upload, CRUD, and processing status."""

import logging
import math
import os
from datetime import datetime
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import String as sqlalchemy_String
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.paper import Paper, ProcessingStatus
from app.models.paper_chunk import PaperChunk
from app.models.user import User
from app.models.workspace import Workspace
from app.routers.workspaces import verify_workspace_ownership
from app.schemas.common import PaginatedResponse
from app.schemas.paper import (
    PaperChunkResponse,
    PaperResponse,
    PaperStatusResponse,
    PaperUpdate,
    PaperUploadResponse,
)
from app.services import paper_service
from app.utils.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Papers"])

MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt"}
ALLOWED_MIME_TYPES: set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


async def verify_paper_access(paper_id: str, user_id: str, db: AsyncSession) -> Paper:
    """Verify that a paper exists and the user owns its parent workspace.

    Args:
        paper_id: The UUID of the paper.
        user_id: The UUID of the user to verify access for.
        db: The async database session.

    Returns:
        The Paper instance if access is confirmed.

    Raises:
        HTTPException: 404 if paper not found, 403 if user does not own workspace.
    """
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()

    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    # Verify the user owns the workspace containing this paper
    ws_result = await db.execute(
        select(Workspace).where(Workspace.id == paper.workspace_id)
    )
    workspace = ws_result.scalar_one_or_none()

    if workspace is None or workspace.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this paper",
        )

    return paper


def _build_paper_response(paper: Paper, chunk_count: int = 0) -> PaperResponse:
    """Build a PaperResponse from a Paper model instance."""
    return PaperResponse(
        id=paper.id,
        title=paper.title,
        authors=paper.authors,
        abstract=paper.abstract,
        file_name=paper.file_name,
        file_size=paper.file_size,
        mime_type=paper.mime_type,
        workspace_id=paper.workspace_id,
        uploaded_by=paper.uploaded_by,
        year=paper.year,
        journal=paper.journal,
        doi=paper.doi,
        tags=paper.tags,
        is_processed=paper.is_processed,
        processing_status=paper.processing_status.value
        if isinstance(paper.processing_status, ProcessingStatus)
        else paper.processing_status,
        processing_error=paper.processing_error,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
        chunk_count=chunk_count,
    )


async def _get_chunk_count(paper_id: str, db: AsyncSession) -> int:
    """Get the number of chunks for a given paper."""
    result = await db.execute(
        select(func.count())
        .select_from(PaperChunk)
        .where(PaperChunk.paper_id == paper_id)
    )
    return result.scalar_one()


async def _process_paper_background(paper_id: str) -> None:
    """Background task to process an uploaded paper.

    This imports processing_service at call time to avoid circular imports
    and to allow the processing service to be implemented independently.
    """
    try:
        from app.services.processing_service import process_paper

        await process_paper(paper_id)
    except ImportError:
        logger.warning(
            "processing_service.process_paper not available; "
            "paper %s will remain in PENDING status.",
            paper_id,
        )
    except Exception:
        logger.exception("Background processing failed for paper %s", paper_id)


@router.get(
    "/workspaces/{workspace_id}/papers",
    response_model=PaginatedResponse[PaperResponse],
)
async def list_papers(
    workspace_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search in title and authors"),
    year: int | None = Query(None, ge=1900, le=2100, description="Filter by year"),
    tags: str | None = Query(None, description="Comma-separated tags to filter by"),
    sort_by: str = Query(
        "created_at", description="Sort field: created_at, title, year"
    ),
    order: str = Query("desc", description="Sort order: asc or desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[PaperResponse]:
    """List papers in a workspace with filtering, search, and pagination."""
    await verify_workspace_ownership(workspace_id, current_user.id, db)

    # Base filter
    conditions = [Paper.workspace_id == workspace_id]

    # Search filter (case-insensitive LIKE on title and authors)
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            Paper.title.ilike(search_pattern)
            | func.cast(Paper.authors, sqlalchemy_String()).ilike(search_pattern)
        )

    # Year filter
    if year is not None:
        conditions.append(Paper.year == year)

    # Tags filter
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for tag in tag_list:
            # JSON column; use LIKE on the serialized representation
            conditions.append(
                func.cast(Paper.tags, sqlalchemy_String()).ilike(f"%{tag}%")
            )

    # Build count query
    count_query = select(func.count()).select_from(Paper)
    for cond in conditions:
        count_query = count_query.where(cond)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Determine sort column
    sort_column_map = {
        "created_at": Paper.created_at,
        "title": Paper.title,
        "year": Paper.year,
    }
    sort_col = sort_column_map.get(sort_by, Paper.created_at)
    if order.lower() == "asc":
        sort_expr = sort_col.asc()
    else:
        sort_expr = sort_col.desc()

    # Fetch papers
    offset = (page - 1) * size
    papers_query = select(Paper).offset(offset).limit(size).order_by(sort_expr)
    for cond in conditions:
        papers_query = papers_query.where(cond)

    result = await db.execute(papers_query)
    papers = result.scalars().all()

    # Build responses with chunk counts
    items: list[PaperResponse] = []
    for paper in papers:
        chunk_count = await _get_chunk_count(paper.id, db)
        items.append(_build_paper_response(paper, chunk_count))

    pages_total = math.ceil(total / size) if total > 0 else 1

    return PaginatedResponse[PaperResponse](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages_total,
    )


@router.post(
    "/workspaces/{workspace_id}/papers/upload",
    response_model=PaperUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_paper(
    workspace_id: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaperUploadResponse:
    """Upload a paper file to a workspace and start background processing."""
    await verify_workspace_ownership(workspace_id, current_user.id, db)

    # Validate filename and extension
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Validate MIME type
    content_type = file.content_type or ""
    mime_type = paper_service.get_mime_type(filename)
    if content_type not in ALLOWED_MIME_TYPES and mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type '{content_type}'.",
        )

    # Validate file size — read headers first, then check after save
    # We trust content-length header as a preliminary check if available
    if file.size is not None and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {MAX_FILE_SIZE_MB} MB.",
        )

    # Save the file to disk
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    file_path, file_size = await paper_service.save_uploaded_file(
        file, workspace_id, upload_dir
    )

    # Post-save size check (in case content-length was missing/incorrect)
    if file_size > MAX_FILE_SIZE_BYTES:
        # Clean up the oversized file
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size ({file_size} bytes) exceeds maximum of {MAX_FILE_SIZE_MB} MB.",
        )

    # Create Paper record
    paper = Paper(
        title=Path(filename).stem or "Untitled Paper",
        file_path=file_path,
        file_name=filename,
        file_size=file_size,
        mime_type=mime_type,
        workspace_id=workspace_id,
        uploaded_by=current_user.id,
        processing_status=ProcessingStatus.PENDING,
    )
    db.add(paper)
    await db.flush()
    await db.refresh(paper)

    # Trigger background processing
    background_tasks.add_task(_process_paper_background, paper.id)

    return PaperUploadResponse(
        id=paper.id,
        file_name=paper.file_name,
        processing_status=paper.processing_status.value,
        message="Paper uploaded successfully. Processing started.",
    )


@router.get("/papers/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaperResponse:
    """Get detailed information about a specific paper."""
    paper = await verify_paper_access(paper_id, current_user.id, db)
    chunk_count = await _get_chunk_count(paper.id, db)
    return _build_paper_response(paper, chunk_count)


@router.put("/papers/{paper_id}", response_model=PaperResponse)
async def update_paper(
    paper_id: str,
    data: PaperUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaperResponse:
    """Update a paper's metadata."""
    paper = await verify_paper_access(paper_id, current_user.id, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(paper, field, value)

    paper.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(paper)

    chunk_count = await _get_chunk_count(paper.id, db)
    return _build_paper_response(paper, chunk_count)


@router.delete(
    "/papers/{paper_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a paper, its chunks, and its file from disk."""
    paper = await verify_paper_access(paper_id, current_user.id, db)

    # Delete file from disk
    if paper.file_path:
        try:
            os.remove(paper.file_path)
        except OSError:
            logger.warning("Could not delete file at %s", paper.file_path)

    await db.delete(paper)
    await db.flush()


@router.get("/papers/{paper_id}/status", response_model=PaperStatusResponse)
async def get_paper_status(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaperStatusResponse:
    """Check the processing status of a paper."""
    paper = await verify_paper_access(paper_id, current_user.id, db)

    return PaperStatusResponse(
        id=paper.id,
        processing_status=paper.processing_status.value
        if isinstance(paper.processing_status, ProcessingStatus)
        else paper.processing_status,
        processing_error=paper.processing_error,
        is_processed=paper.is_processed,
    )


@router.get("/papers/{paper_id}/download")
async def download_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Download the original uploaded file for a paper."""
    paper = await verify_paper_access(paper_id, current_user.id, db)

    if not paper.file_path or not os.path.exists(paper.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        path=paper.file_path,
        filename=paper.file_name,
        media_type=paper.mime_type,
    )


@router.get(
    "/papers/{paper_id}/chunks",
    response_model=list[PaperChunkResponse],
)
async def get_paper_chunks(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PaperChunkResponse]:
    """Get all text chunks for a paper, ordered by chunk index."""
    await verify_paper_access(paper_id, current_user.id, db)

    result = await db.execute(
        select(PaperChunk)
        .where(PaperChunk.paper_id == paper_id)
        .order_by(PaperChunk.chunk_index.asc())
    )
    chunks = result.scalars().all()

    return [
        PaperChunkResponse(
            id=chunk.id,
            paper_id=chunk.paper_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
        )
        for chunk in chunks
    ]
