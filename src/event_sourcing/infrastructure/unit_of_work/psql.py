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
        try:
            # Log the objects in the session before commit
            logger.debug(
                f"Session has {len(self.db.new)} new objects to insert"
            )
            for obj in self.db.new:
                logger.debug(
                    f"New object in session: {type(obj).__name__} - {obj}"
                )

            await self.db.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error(f"Error during commit: {e}")
            raise
