import logging

from event_sourcing.application.projections.base import Projection
from event_sourcing.dto import EventDTO
from event_sourcing.dto.user import UserReadModelData
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class PasswordResetCompletedProjection(Projection):
    """Projection for handling PASSWORD_RESET_COMPLETED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle PASSWORD_RESET_COMPLETED event"""
        try:
            # Extract user data from event
            user_data = UserReadModelData(
                aggregate_id=str(event.aggregate_id),
                password_hash=event.data.password_hash,
                updated_at=event.timestamp,
            )

            # Save to read model
            await self.read_model.save_user(user_data)

            logger.info(
                f"Completed password reset for user: {event.aggregate_id}"
            )

        except Exception as e:
            logger.error(f"Error in PasswordResetCompletedProjection: {e}")
            raise
