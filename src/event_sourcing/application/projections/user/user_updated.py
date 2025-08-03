import logging

from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class UserUpdatedProjection:
    """Projection for handling USER_UPDATED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle USER_UPDATED event"""
        try:
            # Extract update data from event
            update_data = {
                "aggregate_id": str(event.aggregate_id),
                "updated_at": event.timestamp,
            }

            # Add only the fields that were updated
            if "first_name" in event.data:
                update_data["first_name"] = event.data["first_name"]
            if "last_name" in event.data:
                update_data["last_name"] = event.data["last_name"]
            if "email" in event.data:
                update_data["email"] = event.data["email"]

            # Update read model
            await self.read_model.update_user(update_data)

            logger.info(f"Updated user read model for: {event.aggregate_id}")

        except Exception as e:
            logger.error(f"Error in UserUpdatedProjection: {e}")
            raise
