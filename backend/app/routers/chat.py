"""Chat router for AI-powered conversations, paper analysis, and synthesis."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.paper import Paper
from app.models.user import User
from app.models.workspace import Workspace
from app.agents.research_agent import ResearchAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.routers.workspaces import verify_workspace_ownership
from app.schemas.message import (
    AnalysisRequest,
    AnalysisResponse,
    ChatResponse,
    MessageCreate,
    SynthesisRequest,
    SynthesisResponse,
)
from app.services.conversation_service import (
    get_conversation_history,
    save_message,
)
from app.services.embedding_service import embedding_service
from app.utils.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Chat"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _verify_conversation_ownership(
    conversation_id: str,
    user_id: str,
    db: AsyncSession,
) -> Conversation:
    """Verify conversation exists and user owns the parent workspace."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

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


async def _verify_paper_access(
    paper_id: str,
    user_id: str,
    db: AsyncSession,
) -> Paper:
    """Verify paper exists and user owns the parent workspace."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()

    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatResponse,
)
async def send_message(
    conversation_id: str,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ChatResponse:
    """Send a user message and get an AI response.

    1. Save the user message to the database.
    2. Retrieve conversation history.
    3. Run ResearchAgent.analyze() with RAG context.
    4. Save the assistant message (with sources in msg_metadata).
    5. Return ChatResponse.
    """
    conversation = await _verify_conversation_ownership(
        conversation_id, current_user.id, db
    )

    # 1. Save user message
    user_message = await save_message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=data.content,
        db=db,
    )
    logger.info("[AGENT] User message saved: %s", user_message.id)

    # 2. Get conversation history (excluding the message we just saved,
    #    since the agent receives the current query separately)
    history = await get_conversation_history(conversation_id, db, limit=20)
    # Remove the last entry (the message we just saved) so it isn't duplicated
    if history and history[-1].get("content") == data.content:
        history = history[:-1]

    # Determine paper scope: use message-level paper_ids, fall back to conversation-level
    paper_ids: list[str] | None = data.paper_ids or conversation.paper_ids

    # 3. Run ResearchAgent
    agent = ResearchAgent()
    agent_response = agent.analyze(
        query=data.content,
        conversation_history=history,
        workspace_id=conversation.workspace_id,
        paper_ids=paper_ids,
        embedding_service=embedding_service,
    )

    # 4. Save assistant message with sources in msg_metadata
    assistant_metadata: dict = {
        "sources": agent_response.sources,
        "tokens_used": agent_response.tokens_used,
    }
    assistant_message = await save_message(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=agent_response.content,
        db=db,
        msg_metadata=assistant_metadata,
        tokens_used=agent_response.tokens_used,
    )

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    await db.flush()

    logger.info(
        "[AGENT] Assistant response saved: %s (tokens: %d, sources: %d)",
        assistant_message.id,
        agent_response.tokens_used,
        len(agent_response.sources),
    )

    return ChatResponse(
        message_id=assistant_message.id,
        content=agent_response.content,
        sources=agent_response.sources,
        tokens_used=agent_response.tokens_used,
    )


@router.post(
    "/papers/{paper_id}/analyze",
    response_model=AnalysisResponse,
)
async def analyze_paper(
    paper_id: str,
    data: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AnalysisResponse:
    """Trigger a deep analysis on a single paper.

    Supported analysis types: summary, key_findings, methodology, critique, concepts.
    """
    paper = await _verify_paper_access(paper_id, current_user.id, db)

    logger.info(
        "[AGENT] Analysis request: type=%s paper='%s' (%s)",
        data.analysis_type,
        paper.title,
        paper_id,
    )

    agent = AnalysisAgent()
    agent_response = await agent.analyze_paper(
        paper_id=paper_id,
        analysis_type=data.analysis_type,
        db=db,
    )

    logger.info(
        "[AGENT] Analysis complete: type=%s tokens=%d",
        data.analysis_type,
        agent_response.tokens_used,
    )

    return AnalysisResponse(
        result=agent_response.content,
        analysis_type=data.analysis_type,
        tokens_used=agent_response.tokens_used,
    )


@router.post(
    "/workspaces/{workspace_id}/synthesize",
    response_model=SynthesisResponse,
)
async def synthesize_papers(
    workspace_id: str,
    data: SynthesisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SynthesisResponse:
    """Perform cross-paper synthesis within a workspace.

    Supported synthesis types: compare, themes, timeline, gaps.
    Requires at least 2 paper IDs.
    """
    await verify_workspace_ownership(workspace_id, current_user.id, db)

    logger.info(
        "[AGENT] Synthesis request: type=%s papers=%s workspace=%s",
        data.synthesis_type,
        data.paper_ids,
        workspace_id,
    )

    agent = SynthesisAgent()
    agent_response = await agent.synthesize(
        paper_ids=data.paper_ids,
        synthesis_type=data.synthesis_type,
        workspace_id=workspace_id,
        db=db,
        embedding_service=embedding_service,
    )

    logger.info(
        "[AGENT] Synthesis complete: type=%s tokens=%d papers=%s",
        data.synthesis_type,
        agent_response.tokens_used,
        agent_response.sources,
    )

    return SynthesisResponse(
        result=agent_response.content,
        synthesis_type=data.synthesis_type,
        papers_used=agent_response.sources,
        tokens_used=agent_response.tokens_used,
    )
