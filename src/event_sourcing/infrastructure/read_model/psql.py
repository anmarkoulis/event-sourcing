import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.dto.user import UserDTO, UserReadModelData
from event_sourcing.enums import Role
from event_sourcing.exceptions import MissingRequiredFieldError
from event_sourcing.infrastructure.database.models.read.user import User
from event_sourcing.infrastructure.read_model.base import ReadModel

logger = logging.getLogger(__name__)


class PostgreSQLReadModel(ReadModel):
    """PostgreSQL implementation of read model"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_user(self, user_data: UserReadModelData) -> None:
        """Save user to read model"""
        logger.debug(f"Saving user {user_data.aggregate_id} to read model")

        if not user_data.aggregate_id:
            raise MissingRequiredFieldError("aggregate_id", "user data")

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
            if user_data.role is not None:
                existing_user.role = user_data.role
            # updated_at is handled by the UpdatedAtMixin
        else:
            # Create new user
            user_model = User(
                id=user_data.aggregate_id,  # Use aggregate_id as the id
                username=user_data.username,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                role=user_data.role
                or Role.USER,  # Default to USER role if not specified
            )
            self.session.add(user_model)

        # Note: No commit here - UoW will handle it
        logger.debug(f"User {user_data.aggregate_id} saved to session")

    async def get_user(self, user_id: str) -> Optional[UserDTO]:
        """Get a specific user by ID"""
        logger.debug(f"Getting user {user_id}")

        query = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),  # Exclude deleted users
        )

        result = await self.session.execute(query)
        user_model = result.scalar_one_or_none()

        if not user_model:
            logger.debug(f"User {user_id} not found")
            return None

        user_dto = UserDTO(
            id=user_model.id,  # id is now the aggregate_id
            username=user_model.username,
            email=user_model.email,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            role=user_model.role,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
        )

        logger.debug(f"Retrieved user {user_id}")
        return user_dto

    async def get_user_by_username(self, username: str) -> Optional[UserDTO]:
        """Get a specific user by username.

        :param username: Username to search for.
        :return: User DTO if found, None otherwise.
        """
        logger.debug(f"Getting user by username: {username}")

        query = select(User).where(
            User.username == username,
            User.deleted_at.is_(None),  # Exclude deleted users
        )

        result = await self.session.execute(query)
        user_model = result.scalar_one_or_none()

        if not user_model:
            logger.debug(f"User with username {username} not found")
            return None

        user_dto = UserDTO(
            id=user_model.id,
            username=user_model.username,
            email=user_model.email,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            role=user_model.role,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
        )

        logger.debug(f"Retrieved user by username: {username}")
        return user_dto

    async def delete_user(self, user_id: str) -> None:
        """Delete user from read model"""
        logger.debug(f"Deleting user {user_id} from read model")

        await self._delete_user_with_session(user_id)

    async def _delete_user_with_session(self, user_id: str) -> None:
        """Delete user using the session from constructor"""
        # Query by id (which is now the aggregate_id)
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.deleted_at = datetime.now(timezone.utc)
            # Note: No commit here - UoW will handle it
            logger.debug(f"User {user_id} marked for deletion in session")
        else:
            logger.warning(f"User {user_id} not found for deletion")

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 10,
        username: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Tuple[List[UserDTO], int]:
        """List users with pagination and optional filtering"""
        logger.debug(f"Listing users: page={page}, page_size={page_size}")

        # Build base query - exclude deleted users
        base_query = select(User).where(User.deleted_at.is_(None))

        # Add filters if provided
        if username:
            base_query = base_query.where(User.username.ilike(f"%{username}%"))
            logger.debug(f"Filtering by username: {username}")

        if email:
            base_query = base_query.where(User.email.ilike(f"%{email}%"))
            logger.debug(f"Filtering by email: {email}")

        # Count total matching users
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar() or 0  # Ensure it's always an int

        # Get paginated results
        offset = (page - 1) * page_size
        users_query = base_query.offset(offset).limit(page_size)
        users_result = await self.session.execute(users_query)
        users = users_result.scalars().all()

        # Convert to DTOs
        user_dtos = [
            UserDTO(
                id=user.id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ]

        logger.debug(
            f"Retrieved {len(user_dtos)} users out of {total_count} total"
        )
        return user_dtos, total_count
