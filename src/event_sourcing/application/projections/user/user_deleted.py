import logging

from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class UserDeletedProjection:
    """Projection for handling USER_DELETED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle USER_DELETED event"""
        try:
            # Mark user as deleted
            update_data = {
                "aggregate_id": str(event.aggregate_id),
                "status": "deleted",
                "deleted_at": event.timestamp,
                "updated_at": event.timestamp,
            }

            # Update read model
            await self.read_model.update_user(update_data)

            logger.info(f"Marked user as deleted: {event.aggregate_id}")

        except Exception as e:
            logger.error(f"Error in UserDeletedProjection: {e}")
            raise
