import logging

from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class UserCreatedProjection:
    """Projection for handling USER_CREATED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle USER_CREATED event"""
        try:
            # Extract user data from event
            user_data = {
                "aggregate_id": str(event.aggregate_id),
                "username": event.data.get("username"),
                "email": event.data.get("email"),
                "first_name": event.data.get("first_name"),
                "last_name": event.data.get("last_name"),
                "password_hash": event.data.get("password_hash"),
                "status": event.data.get("status"),
                "created_at": event.timestamp,
                "updated_at": event.timestamp,
            }

            # Save to read model
            await self.read_model.save_user(user_data)

            logger.info(
                f"Created user read model for: {user_data['username']}"
            )

        except Exception as e:
            logger.error(f"Error in UserCreatedProjection: {e}")
            raise
