import logging
from abc import ABC, abstractmethod
from typing import Optional

from event_sourcing.dto.user import UserDTO, UserReadModelData

logger = logging.getLogger(__name__)


class ReadModel(ABC):
    """Abstract read model interface"""

    @abstractmethod
    async def save_user(self, user_data: UserReadModelData) -> None:
        """Save user to read model"""

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[UserDTO]:
        """Get a specific user by ID"""

    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        """Delete user from read model"""
