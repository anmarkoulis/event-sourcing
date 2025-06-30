import logging
from typing import Optional

from event_sourcing.application.queries.base import GetClientQuery
from event_sourcing.dto.client import ClientDTO
from event_sourcing.infrastructure.read_model import ReadModel

logger = logging.getLogger(__name__)


class GetClientQueryHandler:
    """Handler for getting a specific client by ID"""

    def __init__(self, read_model: ReadModel):
        self.read_model = read_model

    async def handle(self, query: GetClientQuery) -> Optional[ClientDTO]:
        """Handle get client query"""
        logger.info(f"Getting client: {query.client_id}")

        client = await self.read_model.get_client(query.client_id)

        if client:
            logger.info(f"Successfully retrieved client: {query.client_id}")
        else:
            logger.info(f"Client not found: {query.client_id}")

        return client
