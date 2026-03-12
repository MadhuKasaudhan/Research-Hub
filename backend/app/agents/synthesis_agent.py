"""Synthesis agent for cross-paper analysis."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base_agent import BaseAgent, AgentResponse
from app.models.paper import Paper
from app.models.paper_chunk import PaperChunk
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

SYNTHESIS_PROMPTS: dict[str, str] = {
    "compare": """Compare and contrast the following research papers. Address:
1. Research questions and objectives — how do they differ or overlap?
2. Methodological approaches — similarities and differences
3. Key findings — where do they agree or disagree?
4. Theoretical frameworks used
5. Strengths and weaknesses of each paper relative to others
6. Overall contribution of each paper to the field

Clearly attribute each point to the specific paper(s) it relates to.""",
    "themes": """Identify and analyze common themes across the following research papers:
1. List each major theme found across multiple papers
2. For each theme, explain how different papers address it
3. Note areas of consensus and divergence
4. Identify overarching patterns or trends
5. Discuss how the themes connect to broader research trends

Reference specific papers when discussing each theme.""",
    "timeline": """Build a research evolution timeline based on the following papers:
1. Order the key developments and findings chronologically
2. Show how ideas evolved from one paper to another
3. Identify paradigm shifts or methodological advances
4. Note how later papers build upon or challenge earlier work
5. Identify the trajectory of the research field

Reference specific papers and their publication years when available.""",
    "gaps": """Identify research gaps across the following papers:
1. What questions remain unanswered across all papers?
2. What methodological limitations are common?
3. What populations, contexts, or variables are underexplored?
4. Where do the papers' findings conflict, requiring resolution?
5. What future research directions are suggested?
6. What practical applications remain unexplored?

Be specific and actionable in identifying gaps, referencing the papers.""",
}


class SynthesisAgent(BaseAgent):
    """Agent for cross-paper synthesis and analysis."""

    async def synthesize(
        self,
        paper_ids: list[str],
        synthesis_type: str,
        workspace_id: str,
        db: AsyncSession,
        embedding_service: EmbeddingService,
    ) -> AgentResponse:
        """Perform cross-paper synthesis.

        Args:
            paper_ids: List of paper IDs to synthesize across
            synthesis_type: One of: compare, themes, timeline, gaps
            workspace_id: Workspace ID for context
            db: Database session
            embedding_service: For retrieving relevant chunks

        Returns:
            AgentResponse with synthesis result
        """
        if synthesis_type not in SYNTHESIS_PROMPTS:
            return AgentResponse(
                content=f"Unknown synthesis type: {synthesis_type}. Valid types: {', '.join(SYNTHESIS_PROMPTS.keys())}",
                sources=[],
                tokens_used=0,
            )

        # Get papers info
        result = await db.execute(select(Paper).where(Paper.id.in_(paper_ids)))
        papers = result.scalars().all()

        if len(papers) < 2:
            return AgentResponse(
                content="At least 2 processed papers are required for synthesis.",
                sources=[],
                tokens_used=0,
            )

        # Build context from each paper's key chunks
        context_parts: list[str] = []
        paper_titles: list[str] = []

        for paper in papers:
            paper_titles.append(paper.title)

            # Get chunks for this paper (limit to first 8 for context size)
            chunks_result = await db.execute(
                select(PaperChunk)
                .where(PaperChunk.paper_id == paper.id)
                .order_by(PaperChunk.chunk_index)
                .limit(8)
            )
            chunks = chunks_result.scalars().all()

            paper_text = "\n".join(c.content for c in chunks)
            if len(paper_text) > 4000:
                paper_text = paper_text[:4000] + "\n[Truncated...]"

            paper_header = f"=== Paper: {paper.title} ==="
            if paper.authors:
                authors = (
                    ", ".join(paper.authors)
                    if isinstance(paper.authors, list)
                    else str(paper.authors)
                )
                paper_header += f"\nAuthors: {authors}"
            if paper.year:
                paper_header += f"\nYear: {paper.year}"

            context_parts.append(f"{paper_header}\n\n{paper_text}")

        separator = "\n\n" + "=" * 60 + "\n\n"
        context = separator.join(context_parts)

        logger.info(
            "[AGENT] SynthesisAgent: Running %s synthesis across %d papers: %s",
            synthesis_type,
            len(papers),
            ", ".join(paper_titles),
        )

        system_prompt = f"You are an expert academic researcher performing cross-paper synthesis and analysis.\n\n{SYNTHESIS_PROMPTS[synthesis_type]}"

        response = self.run(
            prompt=f"Please perform a {synthesis_type} synthesis of the {len(papers)} papers provided in the context.",
            system_prompt=system_prompt,
            context=context,
            max_tokens=4096,
        )

        response.sources = paper_titles
        return response
