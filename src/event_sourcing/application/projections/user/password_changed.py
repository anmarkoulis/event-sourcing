import logging

from event_sourcing.application.projections.base import Projection
from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class PasswordChangedProjection(Projection):
    """Projection for handling PASSWORD_CHANGED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle PASSWORD_CHANGED event"""
        try:
            # Extract user data from event
            user_data = {
                "aggregate_id": str(event.aggregate_id),
                "password_hash": event.data.get("new_password_hash"),
                "updated_at": event.timestamp,
            }

            # Save to read model
            await self.read_model.save_user(user_data)

            logger.info(f"Changed password for user: {event.aggregate_id}")

        except Exception as e:
            logger.error(f"Error in PasswordChangedProjection: {e}")
            raise
