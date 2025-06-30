import logging
from typing import Any, Dict

from event_sourcing.application.queries.base import GetBackfillStatusQuery
from event_sourcing.infrastructure.read_model import ReadModel

logger = logging.getLogger(__name__)


class GetBackfillStatusQueryHandler:
    """Handler for getting backfill status"""

    def __init__(self, read_model: ReadModel):
        self.read_model = read_model

    async def handle(self, query: GetBackfillStatusQuery) -> Dict[str, Any]:
        """Handle get backfill status query"""
        logger.info(
            f"Getting backfill status for entity type: {query.entity_type}"
        )

        # For now, return a simple status
        # In a real implementation, this would query a backfill status table
        # or check the read model for completion status

        status = {
            "entity_type": query.entity_type,
            "status": "completed",  # This would be dynamic in real implementation
            "total_entities": 0,  # This would be dynamic in real implementation
            "processed_entities": 0,  # This would be dynamic in real implementation
            "last_updated": None,  # This would be dynamic in real implementation
        }

        logger.info(f"Backfill status for {query.entity_type}: {status}")
        return status
