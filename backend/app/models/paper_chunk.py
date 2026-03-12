"""PaperChunk model for storing text chunks linked to vector embeddings."""

import uuid
from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PaperChunk(Base):
    __tablename__ = "paper_chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    paper_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("papers.id"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chroma_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<PaperChunk paper={self.paper_id} index={self.chunk_index}>"
