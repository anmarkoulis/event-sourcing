import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager for the event sourcing system"""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            echo=False,  # Set to True for SQL debugging
        )
        self.async_session = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def get_session(self) -> AsyncSession:
        """Get a new database session"""
        return self.async_session()

    async def close(self) -> None:
        """Close the database engine"""
        await self.engine.dispose()
        logger.info("Database engine closed")


class AsyncDBContextManager:
    """Context manager for database sessions"""

    def __init__(self, database_manager: DatabaseManager) -> None:
        self.database_manager = database_manager
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        self.session = await self.database_manager.get_session()
        return self.session

    async def __aexit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> None:
        if self.session:
            await self.session.close()
            logger.debug("Database session closed")
