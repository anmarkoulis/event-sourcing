import logging

from event_sourcing.application.projections.base import Projection
from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class UserDeletedProjection(Projection):
    """Projection for handling USER_DELETED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle USER_DELETED event"""
        try:
            # Delete from read model
            await self.read_model.delete_user(str(event.aggregate_id))

            logger.info(f"Marked user as deleted: {event.aggregate_id}")

        except Exception as e:
            logger.error(f"Error in UserDeletedProjection: {e}")
            raise
