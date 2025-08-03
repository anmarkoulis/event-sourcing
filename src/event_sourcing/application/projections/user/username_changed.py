import logging

from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class UsernameChangedProjection:
    """Projection for handling USERNAME_CHANGED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle USERNAME_CHANGED event"""
        try:
            # Update username
            update_data = {
                "aggregate_id": str(event.aggregate_id),
                "username": event.data.get("new_username"),
                "updated_at": event.timestamp,
            }

            # Update read model
            await self.read_model.update_user(update_data)

            logger.info(f"Changed username for user: {event.aggregate_id}")

        except Exception as e:
            logger.error(f"Error in UsernameChangedProjection: {e}")
            raise
