import logging

from event_sourcing.application.commands.aggregate import (
    PublishSnapshotCommand,
)
from event_sourcing.infrastructure.messaging import EventPublisher

logger = logging.getLogger(__name__)


class PublishSnapshotCommandHandler:
    """Handler for publishing aggregate snapshots to external systems"""

    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher

    async def handle(self, command: PublishSnapshotCommand) -> None:
        """Handle publish snapshot command"""
        aggregate_id = command.aggregate_id
        aggregate_type = command.aggregate_type
        snapshot = command.snapshot
        event_type = command.event_type

        logger.info(
            f"Publishing snapshot for: {aggregate_type} {aggregate_id} ({event_type})"
        )

        # Add metadata to snapshot
        enriched_snapshot = {
            **snapshot,
            "event_type": event_type,
            "published_at": "",  # We'll need to handle this differently
            "command_id": "",  # We'll need to handle this differently
        }

        # Publish to external systems
        await self.event_publisher.publish(enriched_snapshot)

        logger.info(
            f"Successfully published snapshot for: {aggregate_type} {aggregate_id}"
        )
