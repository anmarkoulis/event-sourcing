import logging

from event_sourcing.application.projections.base import Projection
from event_sourcing.dto import EventDTO
from event_sourcing.dto.user import UserReadModelData
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class UsernameChangedProjection(Projection):
    """Projection for handling USERNAME_CHANGED events"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, event: EventDTO) -> None:
        """Handle USERNAME_CHANGED event"""
        try:
            # Extract user data from event
            user_data = UserReadModelData(
                aggregate_id=str(event.aggregate_id),
                username=event.data.new_username,
                updated_at=event.timestamp,
            )

            # Save to read model
            await self.read_model.save_user(user_data)

            logger.info(f"Changed username for user: {event.aggregate_id}")

        except Exception as e:
            logger.error(f"Error in UsernameChangedProjection: {e}")
            raise
