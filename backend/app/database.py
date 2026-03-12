"""Database configuration and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

# Will be initialized in init_db()
engine = None
async_session_factory = None


class Base(DeclarativeBase):
    pass


async def init_db(database_url: str = "sqlite+aiosqlite:///./researchhub.db") -> None:
    """Initialize database engine and create all tables."""
    global engine, async_session_factory

    connect_args: dict = {}
    if "sqlite" in database_url:
        connect_args = {"check_same_thread": False}

    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args=connect_args,
    )

    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        from app.models import (
            user,
            workspace,
            paper,
            conversation,
            message,
            paper_chunk,
        )  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    if async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
