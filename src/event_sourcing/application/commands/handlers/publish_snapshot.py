import logging
from typing import Dict, Any

from ....infrastructure.messaging import EventPublisher
from ..aggregate import PublishSnapshotCommand

logger = logging.getLogger(__name__)


class PublishSnapshotCommandHandler:
    """Handler for publishing aggregate snapshots to external systems"""
    
    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher
    
    async def handle(self, command: PublishSnapshotCommand) -> None:
        """Handle publish snapshot command"""
        aggregate_id = command.data["aggregate_id"]
        aggregate_type = command.data["aggregate_type"]
        snapshot = command.data["snapshot"]
        event_type = command.data["event_type"]
        
        logger.info(f"Publishing snapshot for: {aggregate_type} {aggregate_id} ({event_type})")
        
        # Add metadata to snapshot
        enriched_snapshot = {
            **snapshot,
            "event_type": event_type,
            "published_at": command.timestamp.isoformat(),
            "command_id": command.command_id
        }
        
        # Publish to external systems
        await self.event_publisher.publish(enriched_snapshot)
        
        logger.info(f"Successfully published snapshot for: {aggregate_type} {aggregate_id}") 