"""Search router for semantic and metadata-based paper search."""

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy import String as sqlalchemy_String
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.paper import Paper
from app.models.user import User
from app.models.workspace import Workspace
from app.routers.workspaces import verify_workspace_ownership
from app.schemas.common import PaginatedResponse
from app.schemas.paper import PaperResponse
from app.services.embedding_service import embedding_service
from app.utils.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["Search"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SearchChunkResult(BaseModel):
    """A single semantic search hit."""

    chunk: str
    score: float
    paper_id: str
    paper_title: str
    chunk_index: int


class SemanticSearchResponse(BaseModel):
    """Response for semantic search."""

    query: str
    results: list[SearchChunkResult]
    total: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{workspace_id}/search",
    response_model=SemanticSearchResponse,
)
async def semantic_search(
    workspace_id: str,
    q: str = Query(..., min_length=1, max_length=1000, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    paper_ids: str | None = Query(
        None, description="Comma-separated paper IDs to scope the search"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SemanticSearchResponse:
    """Perform semantic search across paper chunks in a workspace.

    Uses ChromaDB vector similarity to find the most relevant text chunks
    matching the query.
    """
    await verify_workspace_ownership(workspace_id, current_user.id, db)

    # Parse optional paper_ids filter
    filter_paper_ids: list[str] | None = None
    if paper_ids:
        filter_paper_ids = [pid.strip() for pid in paper_ids.split(",") if pid.strip()]

    logger.info(
        "[AGENT] Semantic search: q='%s' workspace=%s limit=%d paper_ids=%s",
        q,
        workspace_id,
        limit,
        filter_paper_ids,
    )

    results = embedding_service.semantic_search(
        query=q,
        workspace_id=workspace_id,
        n_results=limit,
        paper_ids=filter_paper_ids,
    )

    items = [
        SearchChunkResult(
            chunk=r.chunk,
            score=r.score,
            paper_id=r.paper_id,
            paper_title=r.paper_title,
            chunk_index=r.chunk_index,
        )
        for r in results
    ]

    return SemanticSearchResponse(
        query=q,
        results=items,
        total=len(items),
    )


@router.get(
    "/{workspace_id}/search/papers",
    response_model=PaginatedResponse[PaperResponse],
)
async def search_papers_metadata(
    workspace_id: str,
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[PaperResponse]:
    """Search papers by metadata (title, authors, abstract, tags) with SQL LIKE.

    Results are ordered by relevance heuristic: title match first, then
    abstract match, then author/tag match.
    """
    await verify_workspace_ownership(workspace_id, current_user.id, db)

    search_pattern = f"%{q}%"

    # Build conditions
    conditions = [
        Paper.workspace_id == workspace_id,
        (
            Paper.title.ilike(search_pattern)
            | Paper.abstract.ilike(search_pattern)
            | func.cast(Paper.authors, sqlalchemy_String()).ilike(search_pattern)
            | func.cast(Paper.tags, sqlalchemy_String()).ilike(search_pattern)
        ),
    ]

    # Count
    count_query = select(func.count()).select_from(Paper)
    for cond in conditions:
        count_query = count_query.where(cond)
    total_result = await db.execute(count_query)
    total: int = total_result.scalar_one()

    # Fetch
    offset = (page - 1) * size
    papers_query = (
        select(Paper).order_by(Paper.created_at.desc()).offset(offset).limit(size)
    )
    for cond in conditions:
        papers_query = papers_query.where(cond)

    result = await db.execute(papers_query)
    papers = result.scalars().all()

    from app.routers.papers import _build_paper_response, _get_chunk_count

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
