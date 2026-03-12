"""Background paper processing pipeline."""

import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.paper import Paper, ProcessingStatus
from app.services.paper_service import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    chunk_text,
)
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


async def update_paper_status(
    db: AsyncSession,
    paper_id: str,
    status: ProcessingStatus,
    error: str | None = None,
) -> None:
    """Update paper processing status in the database."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if paper:
        paper.processing_status = status
        if error:
            paper.processing_error = error
        if status == ProcessingStatus.COMPLETED:
            paper.is_processed = True
        await db.commit()
        logger.info("[AGENT] Paper %s status updated to %s", paper_id, status.value)


async def process_paper(paper_id: str) -> None:
    """Main background processing pipeline for an uploaded paper.

    Steps:
    1. Extract text from file
    2. Chunk text into overlapping segments
    3. Generate embeddings and store in ChromaDB
    4. Update paper status to completed
    """
    from app.database import async_session_factory

    if async_session_factory is None:
        logger.error("[AGENT] Database not initialized")
        return

    async with async_session_factory() as db:
        try:
            # Get the paper record
            result = await db.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                logger.error("[AGENT] Paper %s not found", paper_id)
                return

            logger.info(
                "[AGENT] Starting processing pipeline for paper: %s", paper.file_name
            )

            # Step 1: Extract text
            await update_paper_status(db, paper_id, ProcessingStatus.EXTRACTING)

            file_path = paper.file_path
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            pages: list[str] = []
            if paper.mime_type == "application/pdf":
                pages = extract_text_from_pdf(file_path)
            elif (
                paper.mime_type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                pages = extract_text_from_docx(file_path)
            elif paper.mime_type == "text/plain":
                pages = extract_text_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file type: {paper.mime_type}")

            if not pages or all(not p.strip() for p in pages):
                raise ValueError("No text content could be extracted from the file")

            logger.info(
                "[AGENT] Extracted %d pages from %s", len(pages), paper.file_name
            )

            # Step 2: Chunk text
            await update_paper_status(db, paper_id, ProcessingStatus.CHUNKING)
            chunks = chunk_text(pages, chunk_size=800, overlap=150)
            logger.info(
                "[AGENT] Created %d chunks from %s", len(chunks), paper.file_name
            )

            if not chunks:
                raise ValueError("No chunks generated from extracted text")

            # Step 3: Embed and store
            await update_paper_status(db, paper_id, ProcessingStatus.EMBEDDING)
            stored_count = await embedding_service.embed_and_store_chunks(
                paper_id=paper.id,
                workspace_id=paper.workspace_id,
                paper_title=paper.title,
                chunks=chunks,
                db=db,
            )
            logger.info(
                "[AGENT] Stored %d embeddings for %s", stored_count, paper.file_name
            )

            # Step 4: Try to extract metadata from the first chunk using basic heuristics
            # (Groq-based extraction happens in the analysis agent)
            await update_paper_status(db, paper_id, ProcessingStatus.ANALYZING)

            # Basic metadata extraction from text
            full_text = " ".join(pages[:3])  # Use first 3 pages for metadata
            if paper.title == "Untitled Paper" or paper.title == paper.file_name:
                # Try to use first line as title
                first_line = pages[0].strip().split("\n")[0].strip() if pages else ""
                if first_line and len(first_line) < 300:
                    paper.title = first_line

            if not paper.abstract and len(full_text) > 200:
                # Try to find abstract section
                lower_text = full_text.lower()
                abs_start = lower_text.find("abstract")
                if abs_start != -1:
                    abs_text = full_text[abs_start + 8 : abs_start + 2000].strip()
                    # Clean up: take until next section header or limit
                    for marker in ["\nintroduction", "\n1.", "\n1 "]:
                        marker_pos = abs_text.lower().find(marker)
                        if marker_pos > 50:
                            abs_text = abs_text[:marker_pos].strip()
                            break
                    if abs_text:
                        paper.abstract = abs_text[:2000]

            # Step 5: Mark as completed
            paper.processing_status = ProcessingStatus.COMPLETED
            paper.is_processed = True
            paper.processing_error = None
            await db.commit()

            logger.info(
                "[AGENT] Processing completed for paper: %s (%s)", paper.title, paper_id
            )

        except Exception as e:
            logger.error("[AGENT] Processing failed for paper %s: %s", paper_id, str(e))
            try:
                await update_paper_status(
                    db, paper_id, ProcessingStatus.FAILED, error=str(e)
                )
            except Exception as db_error:
                logger.error("[AGENT] Failed to update error status: %s", str(db_error))
