import logging

from event_sourcing.application.projections.base import Projection
from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class PasswordResetRequestedProjection(Projection):
    """Projection for handling PASSWORD_RESET_REQUESTED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle PASSWORD_RESET_REQUESTED event"""
        try:
            # Extract user data from event
            user_data = {
                "aggregate_id": str(event.aggregate_id),
                "reset_token": event.data.get("reset_token"),
                "reset_token_expires": event.data.get("reset_token_expires"),
                "updated_at": event.timestamp,
            }

            # Save to read model
            await self.read_model.save_user(user_data)

            logger.info(
                f"Stored password reset request for user: {event.aggregate_id}"
            )

        except Exception as e:
            logger.error(f"Error in PasswordResetRequestedProjection: {e}")
            raise
