"""Analysis agent for deep single-paper analysis."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base_agent import BaseAgent, AgentResponse
from app.models.paper_chunk import PaperChunk
from app.models.paper import Paper

logger = logging.getLogger(__name__)

ANALYSIS_PROMPTS: dict[str, str] = {
    "summary": """Provide a comprehensive summary of this research paper. Include:
1. The main research question or objective
2. Background and motivation
3. Key methodology used
4. Main findings and results
5. Conclusions and implications
6. Significance of the work

Be thorough but concise. Use academic language.""",
    "key_findings": """Extract and list the key findings and contributions of this research paper. For each finding:
- State the finding clearly
- Provide supporting evidence or data mentioned
- Explain its significance

Format as a numbered list with clear, detailed bullet points.""",
    "methodology": """Extract and explain the methodology used in this research paper in detail:
1. Research design and approach
2. Data collection methods
3. Analysis techniques
4. Tools, frameworks, or instruments used
5. Sample size and selection criteria (if applicable)
6. Limitations of the methodology

Be specific and technical where appropriate.""",
    "critique": """Provide a critical analysis of this research paper. Address:
1. Strengths of the research
2. Weaknesses and limitations
3. Potential biases or confounding factors
4. Gaps in the analysis or methodology
5. Questions left unanswered
6. Suggestions for improvement or future work

Be balanced, objective, and constructive.""",
    "concepts": """Extract and explain the core concepts, theories, and technical terms used in this paper:
1. List each key concept or term
2. Provide a clear definition or explanation
3. Explain how it relates to the paper's research
4. Note any novel concepts introduced by the authors

Format as a structured glossary with detailed explanations.""",
}


class AnalysisAgent(BaseAgent):
    """Agent for deep single-paper analysis."""

    async def analyze_paper(
        self,
        paper_id: str,
        analysis_type: str,
        db: AsyncSession,
    ) -> AgentResponse:
        """Perform deep analysis on a single paper.

        Args:
            paper_id: ID of the paper to analyze
            analysis_type: One of: summary, key_findings, methodology, critique, concepts
            db: Database session

        Returns:
            AgentResponse with the analysis result
        """
        if analysis_type not in ANALYSIS_PROMPTS:
            return AgentResponse(
                content=f"Unknown analysis type: {analysis_type}. Valid types: {', '.join(ANALYSIS_PROMPTS.keys())}",
                sources=[],
                tokens_used=0,
            )

        # Get paper info
        result = await db.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()
        if not paper:
            return AgentResponse(
                content="Paper not found.",
                sources=[],
                tokens_used=0,
            )

        # Get all chunks for the paper
        chunks_result = await db.execute(
            select(PaperChunk)
            .where(PaperChunk.paper_id == paper_id)
            .order_by(PaperChunk.chunk_index)
        )
        chunks = chunks_result.scalars().all()

        if not chunks:
            return AgentResponse(
                content="This paper hasn't been processed yet. Please wait for processing to complete.",
                sources=[paper.title],
                tokens_used=0,
            )

        # Build full text context from chunks (limit to avoid token overflow)
        full_text = "\n\n".join(chunk.content for chunk in chunks)
        # Truncate to ~12000 chars to stay within context limits
        if len(full_text) > 12000:
            full_text = full_text[:12000] + "\n\n[Text truncated for length...]"

        context = f"Paper Title: {paper.title}\n"
        if paper.authors:
            context += f"Authors: {', '.join(paper.authors) if isinstance(paper.authors, list) else str(paper.authors)}\n"
        if paper.year:
            context += f"Year: {paper.year}\n"
        if paper.journal:
            context += f"Journal: {paper.journal}\n"
        context += f"\n--- Full Paper Content ---\n{full_text}"

        logger.info(
            "[AGENT] AnalysisAgent: Running %s analysis on paper '%s' (%d chunks)",
            analysis_type,
            paper.title,
            len(chunks),
        )

        system_prompt = f"You are an expert academic researcher performing a detailed analysis of a research paper.\n\n{ANALYSIS_PROMPTS[analysis_type]}"

        response = self.run(
            prompt=f"Please analyze the following paper and provide a {analysis_type.replace('_', ' ')} analysis.",
            system_prompt=system_prompt,
            context=context,
            max_tokens=4096,
        )

        response.sources = [paper.title]
        return response
