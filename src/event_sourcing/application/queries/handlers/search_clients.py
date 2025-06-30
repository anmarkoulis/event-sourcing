import logging
from typing import List

from event_sourcing.application.queries.base import SearchClientsQuery
from event_sourcing.dto.client import ClientDTO
from event_sourcing.infrastructure.read_model import ReadModel

logger = logging.getLogger(__name__)


class SearchClientsQueryHandler:
    """Handler for searching clients with filtering and pagination"""

    def __init__(self, read_model: ReadModel):
        self.read_model = read_model

    async def handle(self, query: SearchClientsQuery) -> List[ClientDTO]:
        """Handle search clients query"""
        logger.info(f"Searching clients with query: {query}")

        clients: List[ClientDTO] = await self.read_model.search_clients(query)

        logger.info(f"Found {len(clients)} clients")
        return clients
