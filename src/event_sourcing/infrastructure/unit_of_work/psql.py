import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseUnitOfWork

logger = logging.getLogger(__name__)


class SQLAUnitOfWork(BaseUnitOfWork):
    """PostgreSQL Unit of Work using SQLAlchemy AsyncSession"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def rollback(self) -> None:
        logger.debug("Rolling back transaction")
        await self.db.rollback()

    async def commit(self) -> None:
        logger.debug("Committing transaction")
        await self.db.commit()
