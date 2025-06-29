import logging

from event_sourcing.application.commands.aggregate import (
    AsyncPublishSnapshotCommand,
)

logger = logging.getLogger(__name__)


class AsyncPublishSnapshotCommandHandler:
    """Handler for asynchronously publishing snapshots via Celery"""

    def __init__(self) -> None:
        """Initialize the async handler (no dependencies needed as it just triggers Celery)"""

    async def handle(self, command: AsyncPublishSnapshotCommand) -> None:
        """Handle the async command by triggering a Celery task"""
        logger.info(f"Triggering Celery task for publish snapshot command")

        # Extract data from command
        aggregate_id = command.aggregate_id
        aggregate_type = command.aggregate_type
        snapshot = command.snapshot
        event_type = command.event_type

        # Trigger Celery task using dynamic import
        from event_sourcing.application.tasks.publish_snapshot import (
            publish_snapshot_task,
        )

        task = publish_snapshot_task.delay(
            command_id="",  # We'll need to handle this differently
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            snapshot=snapshot,
            event_type=event_type,
        )

        logger.info(f"Celery task triggered with task_id: {task.id}")
