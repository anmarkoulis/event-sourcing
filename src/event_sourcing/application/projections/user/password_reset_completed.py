import logging

from event_sourcing.application.projections.base import Projection
from event_sourcing.dto import EventDTO
from event_sourcing.dto.user import UserReadModelData
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel
from event_sourcing.infrastructure.unit_of_work import BaseUnitOfWork

logger = logging.getLogger(__name__)


class PasswordResetCompletedProjection(Projection):
    """Projection for handling PASSWORD_RESET_COMPLETED events"""

    def __init__(
        self, read_model: PostgreSQLReadModel, unit_of_work: BaseUnitOfWork
    ):
        self.read_model = read_model
        self.unit_of_work = unit_of_work

    async def handle(self, event: EventDTO) -> None:
        """Handle PASSWORD_RESET_COMPLETED event"""
        try:
            # Get current user state from read model to preserve existing fields
            current_user = await self.read_model.get_user(
                str(event.aggregate_id)
            )

            # Extract user data from event, preserving existing fields
            user_data = UserReadModelData(
                aggregate_id=str(event.aggregate_id),
                username=current_user.username
                if current_user
                else None,  # Preserve existing username
                password_hash=event.data.password_hash,  # Update password hash
                updated_at=event.timestamp,
            )

            # Use Unit of Work for transaction management
            async with self.unit_of_work:
                # Save to read model
                await self.read_model.save_user(user_data)
                # UoW will handle commit/rollback

            logger.info(
                f"Updated password reset completed in read model for: {event.aggregate_id}"
            )

        except Exception as e:
            logger.error(f"Error in PasswordResetCompletedProjection: {e}")
            raise
