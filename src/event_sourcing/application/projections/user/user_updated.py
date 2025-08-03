import logging

from event_sourcing.application.projections.base import Projection
from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class UserUpdatedProjection(Projection):
    """Projection for handling USER_UPDATED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle USER_UPDATED event"""
        try:
            # Extract user data from event
            user_data = {
                "aggregate_id": str(event.aggregate_id),
                "first_name": event.data.get("first_name"),
                "last_name": event.data.get("last_name"),
                "email": event.data.get("email"),
                "updated_at": event.timestamp,
            }

            # Save to read model
            await self.read_model.save_user(user_data)

            logger.info(f"Updated user read model for: {event.aggregate_id}")

        except Exception as e:
            logger.error(f"Error in UserUpdatedProjection: {e}")
            raise
