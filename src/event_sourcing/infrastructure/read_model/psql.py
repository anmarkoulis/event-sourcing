import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.dto.user import UserDTO, UserReadModelData
from event_sourcing.infrastructure.database.models.read.user import User

from .base import ReadModel

logger = logging.getLogger(__name__)


class PostgreSQLReadModel(ReadModel):
    """PostgreSQL implementation of read model"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_user(self, user_data: UserReadModelData) -> None:
        """Save user to read model"""
        logger.info(f"Saving user {user_data.aggregate_id} to read model")

        if not user_data.aggregate_id:
            raise ValueError("aggregate_id is required")

        await self._save_user_with_session(user_data)

    async def _save_user_with_session(
        self, user_data: UserReadModelData
    ) -> None:
        """Save user using the session from constructor"""
        # Check if user already exists by id (which is now the aggregate_id)
        result = await self.session.execute(
            select(User).where(User.id == user_data.aggregate_id)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Update existing user
            if user_data.username is not None:
                existing_user.username = user_data.username
            if user_data.email is not None:
                existing_user.email = user_data.email
            if user_data.first_name is not None:
                existing_user.first_name = user_data.first_name
            if user_data.last_name is not None:
                existing_user.last_name = user_data.last_name
            if user_data.password_hash is not None:
                existing_user.password_hash = user_data.password_hash
            if user_data.status is not None:
                existing_user.status = user_data.status
            # updated_at is handled by the UpdatedAtMixin
        else:
            # Create new user
            user_model = User(
                id=user_data.aggregate_id,  # Use aggregate_id as the id
                username=user_data.username,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                password_hash=user_data.password_hash,
                status=user_data.status or "active",
            )
            self.session.add(user_model)

        # Note: No commit here - UoW will handle it
        logger.info(f"User {user_data.aggregate_id} saved to session")

    async def get_user(self, user_id: str) -> Optional[UserDTO]:
        """Get a specific user by ID"""
        logger.info(f"Getting user {user_id}")

        query = select(User).where(User.id == user_id)

        result = await self.session.execute(query)
        user_model = result.scalar_one_or_none()

        if not user_model:
            logger.info(f"User {user_id} not found")
            return None

        user_dto = UserDTO(
            id=user_model.id,  # id is now the aggregate_id
            username=user_model.username,
            email=user_model.email,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            status=user_model.status,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
        )

        logger.info(f"Retrieved user {user_id}")
        return user_dto

    async def delete_user(self, user_id: str) -> None:
        """Delete user from read model"""
        logger.info(f"Deleting user {user_id} from read model")

        await self._delete_user_with_session(user_id)

    async def _delete_user_with_session(self, user_id: str) -> None:
        """Delete user using the session from constructor"""
        # Query by id (which is now the aggregate_id)
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.deleted_at = datetime.utcnow()
            user.status = "deleted"
            # Note: No commit here - UoW will handle it
            logger.info(f"User {user_id} marked for deletion in session")
        else:
            logger.warning(f"User {user_id} not found for deletion")
