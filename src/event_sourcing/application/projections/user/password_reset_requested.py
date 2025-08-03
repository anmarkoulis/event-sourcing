import logging

from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class PasswordResetRequestedProjection:
    """Projection for handling PASSWORD_RESET_REQUESTED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle PASSWORD_RESET_REQUESTED event"""
        try:
            # Store reset token and email for password reset
            reset_data = {
                "aggregate_id": str(event.aggregate_id),
                "email": event.data.get("email"),
                "reset_token": event.data.get("reset_token"),
                "reset_requested_at": event.timestamp,
            }

            # Save reset request to read model
            await self.read_model.save_password_reset_request(reset_data)

            logger.info(
                f"Stored password reset request for user: {event.aggregate_id}"
            )

        except Exception as e:
            logger.error(f"Error in PasswordResetRequestedProjection: {e}")
            raise
