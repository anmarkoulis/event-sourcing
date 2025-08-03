import logging

from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class PasswordResetCompletedProjection:
    """Projection for handling PASSWORD_RESET_COMPLETED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle PASSWORD_RESET_COMPLETED event"""
        try:
            # Update password hash
            update_data = {
                "aggregate_id": str(event.aggregate_id),
                "password_hash": event.data.get("new_password_hash"),
                "updated_at": event.timestamp,
            }

            # Update read model
            await self.read_model.update_user(update_data)

            # Clear the reset request
            await self.read_model.clear_password_reset_request(
                str(event.aggregate_id)
            )

            logger.info(
                f"Completed password reset for user: {event.aggregate_id}"
            )

        except Exception as e:
            logger.error(f"Error in PasswordResetCompletedProjection: {e}")
            raise
