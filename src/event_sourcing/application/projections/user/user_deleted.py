import logging

from event_sourcing.application.projections.base import Projection
from event_sourcing.dto import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel
from event_sourcing.infrastructure.unit_of_work import BaseUnitOfWork

logger = logging.getLogger(__name__)


class UserDeletedProjection(Projection):
    """Projection for handling USER_DELETED events"""

    def __init__(
        self, read_model: PostgreSQLReadModel, unit_of_work: BaseUnitOfWork
    ):
        self.read_model = read_model
        self.unit_of_work = unit_of_work

    async def handle(self, event: EventDTO) -> None:
        """Handle USER_DELETED event"""
        try:
            # Use Unit of Work for transaction management
            async with self.unit_of_work:
                # Delete from read model
                await self.read_model.delete_user(str(event.aggregate_id))
                # UoW will handle commit/rollback

            logger.debug(f"Deleted user read model for: {event.aggregate_id}")

        except Exception as e:
            logger.error(f"Error in UserDeletedProjection: {e}")
            raise
