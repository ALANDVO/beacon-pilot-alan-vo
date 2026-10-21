"""Database connection and session management."""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Database:
    """Database connection manager."""
    
    def __init__(self, database_url: str | None = None):
        self.settings = get_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._database_url = database_url or self.settings.database_url
    
    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(
                self._database_url,
                echo=self.settings.debug,
                future=True,
            )
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._session_factory
    
    @asynccontextmanager
    async def session(self) -> AsyncSession:
        """Get a database session."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def create_all(self) -> None:
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_all(self) -> None:
        """Drop all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def close(self) -> None:
        """Close the database engine."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Global database instance
_db: Database | None = None


def get_database(database_url: str | None = None) -> Database:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        _db = Database(database_url)
    return _db


async def init_db(database_url: str | None = None) -> None:
    """Initialize database connection and create tables."""
    db = get_database(database_url)
    await db.create_all()


async def close_db() -> None:
    """Close database connection."""
    global _db
    if _db:
        await _db.close()
        _db = None