"""Research agent for answering questions about papers using RAG."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import BaseAgent, AgentResponse
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

RESEARCH_SYSTEM_PROMPT = """You are a research assistant AI specializing in academic paper analysis. Your role is to answer questions about research papers based ONLY on the provided context from the papers.

Rules:
1. Answer based ONLY on the provided context from research papers.
2. ALWAYS cite specific papers by their title when referencing information.
3. If the context doesn't contain enough information to answer the question, clearly state: "I don't have enough context in the provided papers to answer this question fully."
4. Be precise, academic in tone, and well-structured in your responses.
5. Use bullet points or numbered lists for clarity when appropriate.
6. When comparing information across papers, clearly attribute each point to its source paper.
7. If asked about methodology, findings, or conclusions, be specific and detailed.
"""


class ResearchAgent(BaseAgent):
    """Agent for RAG-based question answering over research papers."""

    def analyze(
        self,
        query: str,
        conversation_history: list[dict[str, str]],
        workspace_id: str,
        paper_ids: list[str] | None,
        embedding_service: EmbeddingService,
    ) -> AgentResponse:
        """Answer a question using RAG over research papers.

        Steps:
        1. RETRIEVE — Semantic search for relevant chunks
        2. BUILD CONTEXT — Format retrieved chunks with paper attribution
        3. GENERATE — Call Groq with context + history + query
        """
        # Step 1: Retrieve relevant chunks
        logger.info(
            "[AGENT] ResearchAgent: Searching for relevant chunks for query: %s",
            query[:100],
        )
        search_results = embedding_service.semantic_search(
            query=query,
            workspace_id=workspace_id,
            n_results=8,
            paper_ids=paper_ids,
        )

        if not search_results:
            logger.info("[AGENT] ResearchAgent: No relevant chunks found")
            return AgentResponse(
                content="I couldn't find any relevant information in the papers within this workspace. Please make sure papers have been uploaded and processed.",
                sources=[],
                tokens_used=0,
            )

        # Step 2: Build context from retrieved chunks
        context_parts: list[str] = []
        source_titles: set[str] = set()
        for result in search_results:
            context_parts.append(
                f"[Paper: {result.paper_title}] (Relevance: {result.score:.2f})\n{result.chunk}\n---"
            )
            source_titles.add(result.paper_title)

        context = "\n\n".join(context_parts)
        logger.info(
            "[AGENT] ResearchAgent: Built context from %d chunks across %d papers",
            len(search_results),
            len(source_titles),
        )

        # Step 3: Generate response
        response = self.run(
            prompt=query,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            context=context,
            conversation_history=conversation_history,
        )

        response.sources = sorted(source_titles)
        return response
