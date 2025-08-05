import logging
from typing import Optional

from event_sourcing.application.queries.handlers.base import QueryHandler
from event_sourcing.application.queries.user import GetUserQuery
from event_sourcing.dto.user import UserDTO
from event_sourcing.infrastructure.read_model import PostgreSQLReadModel

logger = logging.getLogger(__name__)


class GetUserQueryHandler(QueryHandler[GetUserQuery, UserDTO]):
    """Handler for getting user by ID"""

    def __init__(self, read_model: PostgreSQLReadModel):
        self.read_model = read_model

    async def handle(self, query: GetUserQuery) -> Optional[UserDTO]:
        """Handle get user query"""
        try:
            user = await self.read_model.get_user(str(query.user_id))
            return user
        except Exception as e:
            logger.error(f"Error getting user {query.user_id}: {e}")
            return None
