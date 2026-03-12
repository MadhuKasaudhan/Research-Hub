"""Vector embedding service using ChromaDB with default embeddings."""

import os
import logging
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings as ChromaSettings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.paper_chunk import PaperChunk

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from semantic search."""

    chunk: str
    score: float
    paper_id: str
    paper_title: str
    chunk_index: int


class EmbeddingService:
    """Service for managing vector embeddings in ChromaDB."""

    def __init__(self) -> None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        os.makedirs(persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info(
            "[AGENT] EmbeddingService initialized with ChromaDB at %s", persist_dir
        )

    def get_or_create_collection(self, workspace_id: str) -> chromadb.Collection:
        """Get or create a ChromaDB collection for a workspace."""
        collection_name = f"workspace_{workspace_id.replace('-', '_')}"
        # ChromaDB collection names must be 3-63 chars, alphanumeric + underscores
        return self._client.get_or_create_collection(
            name=collection_name,
            metadata={"workspace_id": workspace_id},
        )

    async def embed_and_store_chunks(
        self,
        paper_id: str,
        workspace_id: str,
        paper_title: str,
        chunks: list[str],
        db: AsyncSession,
    ) -> int:
        """Embed text chunks and store in ChromaDB + SQLite.

        Returns the number of chunks stored.
        """
        if not chunks:
            return 0

        collection = self.get_or_create_collection(workspace_id)

        # Generate unique IDs for each chunk
        chroma_ids = [f"{paper_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "paper_id": paper_id,
                "chunk_index": i,
                "workspace_id": workspace_id,
                "paper_title": paper_title,
            }
            for i in range(len(chunks))
        ]

        # Add to ChromaDB (it will use its default embedding function)
        # Process in batches of 100 to avoid memory issues
        batch_size = 100
        for start in range(0, len(chunks), batch_size):
            end = min(start + batch_size, len(chunks))
            collection.add(
                ids=chroma_ids[start:end],
                documents=chunks[start:end],
                metadatas=metadatas[start:end],
            )

        # Save chunk records to SQLite
        for i, chunk_text in enumerate(chunks):
            chunk_record = PaperChunk(
                paper_id=paper_id,
                chunk_index=i,
                content=chunk_text,
                chroma_id=chroma_ids[i],
            )
            db.add(chunk_record)

        await db.flush()
        logger.info("[AGENT] Stored %d chunks for paper %s", len(chunks), paper_id)
        return len(chunks)

    def semantic_search(
        self,
        query: str,
        workspace_id: str,
        n_results: int = 10,
        paper_ids: list[str] | None = None,
    ) -> list[SearchResult]:
        """Search for relevant chunks using semantic similarity."""
        collection = self.get_or_create_collection(workspace_id)

        # Build where filter
        where_filter = None
        if paper_ids:
            if len(paper_ids) == 1:
                where_filter = {"paper_id": paper_ids[0]}
            else:
                where_filter = {"paper_id": {"$in": paper_ids}}

        try:
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection.count() or 1),
                where=where_filter if where_filter else None,
            )
        except Exception as e:
            logger.error("[AGENT] Semantic search error: %s", str(e))
            return []

        search_results: list[SearchResult] = []
        if results and results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            distances = (
                results["distances"][0]
                if results["distances"]
                else [0.0] * len(documents)
            )
            metadatas = (
                results["metadatas"][0]
                if results["metadatas"]
                else [{}] * len(documents)
            )

            for doc, dist, meta in zip(documents, distances, metadatas):
                # ChromaDB returns distances; convert to similarity score (lower distance = higher similarity)
                score = max(0.0, 1.0 - dist)
                search_results.append(
                    SearchResult(
                        chunk=doc,
                        score=score,
                        paper_id=meta.get("paper_id", ""),
                        paper_title=meta.get("paper_title", "Unknown"),
                        chunk_index=meta.get("chunk_index", 0),
                    )
                )

        return search_results

    def delete_paper_embeddings(self, paper_id: str, workspace_id: str) -> None:
        """Delete all embeddings for a paper from ChromaDB."""
        try:
            collection = self.get_or_create_collection(workspace_id)
            # Get all chunk IDs for this paper
            existing = collection.get(
                where={"paper_id": paper_id},
            )
            if existing and existing["ids"]:
                collection.delete(ids=existing["ids"])
                logger.info(
                    "[AGENT] Deleted %d embeddings for paper %s",
                    len(existing["ids"]),
                    paper_id,
                )
        except Exception as e:
            logger.error(
                "[AGENT] Error deleting embeddings for paper %s: %s", paper_id, str(e)
            )


# Singleton instance
embedding_service = EmbeddingService()
