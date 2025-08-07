import logging
import math
from typing import Any, Dict

from event_sourcing.application.queries.handlers.base import QueryHandler
from event_sourcing.application.queries.user import ListUsersQuery
from event_sourcing.infrastructure.read_model import ReadModel

logger = logging.getLogger(__name__)


class ListUsersQueryHandler(QueryHandler[ListUsersQuery, Dict[str, Any]]):
    """Handler for listing users with pagination"""

    def __init__(self, read_model: ReadModel):
        self.read_model = read_model

    async def handle(self, query: ListUsersQuery) -> Dict[str, Any]:
        """Handle list users query"""
        try:
            # Get users and total count from read model
            users, total_count = await self.read_model.list_users(
                page=query.page,
                page_size=query.page_size,
                username=query.username,
                email=query.email,
            )

            # Calculate pagination info
            total_pages = (
                math.ceil(total_count / query.page_size)
                if total_count > 0
                else 0
            )

            # Build next and previous URLs
            next_url = None
            previous_url = None

            if query.page < total_pages:
                next_url = f"/users/?page={query.page + 1}&page_size={query.page_size}"
                if query.username:
                    next_url += f"&username={query.username}"
                if query.email:
                    next_url += f"&email={query.email}"

            if query.page > 1:
                previous_url = f"/users/?page={query.page - 1}&page_size={query.page_size}"
                if query.username:
                    previous_url += f"&username={query.username}"
                if query.email:
                    previous_url += f"&email={query.email}"

            return {
                "results": users,
                "next": next_url,
                "previous": previous_url,
                "count": total_count,
                "page": query.page,
                "page_size": query.page_size,
            }

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            # Return empty result on error
            return {
                "results": [],
                "next": None,
                "previous": None,
                "count": 0,
                "page": query.page,
                "page_size": query.page_size,
            }
