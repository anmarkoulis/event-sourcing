import logging

from event_sourcing.application.projections.base import Projection
from event_sourcing.dto import EventDTO
from event_sourcing.dto.user import UserReadModelData
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel
from event_sourcing.infrastructure.unit_of_work import BaseUnitOfWork

logger = logging.getLogger(__name__)


class PasswordResetRequestedProjection(Projection):
    """Projection for handling PASSWORD_RESET_REQUESTED events"""

    def __init__(
        self, read_model: PostgreSQLReadModel, unit_of_work: BaseUnitOfWork
    ):
        self.read_model = read_model
        self.unit_of_work = unit_of_work

    async def handle(self, event: EventDTO) -> None:
        """Handle PASSWORD_RESET_REQUESTED event"""
        try:
            # Extract user data from event
            user_data = UserReadModelData(
                aggregate_id=str(event.aggregate_id),
                updated_at=event.timestamp,
            )

            # Use Unit of Work for transaction management
            async with self.unit_of_work:
                # Save to read model
                await self.read_model.save_user(user_data)
                # UoW will handle commit/rollback

            logger.info(
                f"Updated password reset requested in read model for: {event.aggregate_id}"
            )

        except Exception as e:
            logger.error(f"Error in PasswordResetRequestedProjection: {e}")
            raise
