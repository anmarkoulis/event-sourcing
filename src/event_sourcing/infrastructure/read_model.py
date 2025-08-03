import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select

from event_sourcing.dto.user import UserDTO
from event_sourcing.infrastructure.database.models.read.user import User
from event_sourcing.infrastructure.database.session import (
    AsyncDBContextManager,
    DatabaseManager,
)

logger = logging.getLogger(__name__)


class ReadModel(ABC):
    """Abstract read model interface"""

    @abstractmethod
    async def save_user(self, user_data: Dict[str, Any]) -> None:
        """Save user to read model"""

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[UserDTO]:
        """Get a specific user by ID"""

    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        """Delete user from read model"""


class PostgreSQLReadModel(ReadModel):
    """PostgreSQL implementation of read model"""

    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager

    async def save_user(self, user_data: Dict[str, Any]) -> None:
        """Save user to read model"""
        logger.info(
            f"Saving user {user_data.get('aggregate_id')} to read model"
        )

        aggregate_id = user_data.get("aggregate_id")
        if not aggregate_id:
            raise ValueError("aggregate_id is required")

        async with AsyncDBContextManager(self.database_manager) as session:
            # Check if user already exists by aggregate_id
            result = await session.execute(
                select(User).where(User.aggregate_id == aggregate_id)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # Update existing user
                if user_data.get("username") is not None:
                    existing_user.username = user_data.get("username")
                if user_data.get("email") is not None:
                    existing_user.email = user_data.get("email")
                if user_data.get("first_name") is not None:
                    existing_user.first_name = user_data.get("first_name")
                if user_data.get("last_name") is not None:
                    existing_user.last_name = user_data.get("last_name")
                if user_data.get("password_hash") is not None:
                    existing_user.password_hash = user_data.get(
                        "password_hash"
                    )
                if user_data.get("status") is not None:
                    existing_user.status = user_data.get("status")
                existing_user.updated_at_user = datetime.utcnow()
            else:
                # Create new user
                user_model = User(
                    aggregate_id=aggregate_id,
                    username=user_data.get("username"),
                    email=user_data.get("email"),
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name"),
                    password_hash=user_data.get("password_hash"),
                    status=user_data.get("status", "active"),
                    created_at_user=datetime.utcnow(),
                    updated_at_user=datetime.utcnow(),
                )
                session.add(user_model)

            await session.commit()
            logger.info(f"User {aggregate_id} saved successfully")

    async def get_user(self, user_id: str) -> Optional[UserDTO]:
        """Get a specific user by ID"""
        logger.info(f"Getting user {user_id}")

        query = select(User).where(User.aggregate_id == user_id)

        async with AsyncDBContextManager(self.database_manager) as session:
            result = await session.execute(query)
            user_model = result.scalar_one_or_none()

            if not user_model:
                logger.info(f"User {user_id} not found")
                return None

            user_dto = UserDTO(
                id=user_model.aggregate_id,
                username=user_model.username,
                email=user_model.email,
                first_name=user_model.first_name,
                last_name=user_model.last_name,
                status=user_model.status,
                created_at=user_model.created_at_user,
                updated_at=user_model.updated_at_user,
            )

            logger.info(f"Retrieved user {user_id}")
            return user_dto

    async def delete_user(self, user_id: str) -> None:
        """Delete user from read model"""
        logger.info(f"Deleting user {user_id} from read model")

        async with AsyncDBContextManager(self.database_manager) as session:
            # Query by aggregate_id instead of primary key
            result = await session.execute(
                select(User).where(User.aggregate_id == user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.deleted_at = datetime.utcnow()
                user.status = "deleted"
                await session.commit()
                logger.info(f"User {user_id} deleted successfully")
            else:
                logger.warning(f"User {user_id} not found for deletion")
