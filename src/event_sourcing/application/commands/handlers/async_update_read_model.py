import logging

from event_sourcing.application.commands.aggregate import (
    AsyncUpdateReadModelCommand,
)
from event_sourcing.application.tasks.update_read_model import (
    update_read_model_task,
)

logger = logging.getLogger(__name__)


class AsyncUpdateReadModelCommandHandler:
    """Handler for asynchronously updating read models via Celery"""

    def __init__(self) -> None:
        """Initialize the async handler (no dependencies needed as it just triggers Celery)"""

    async def handle(self, command: AsyncUpdateReadModelCommand) -> None:
        """Handle the async command by triggering a Celery task"""
        logger.info(f"Triggering Celery task for update read model command")

        # Extract data from command
        aggregate_id = command.aggregate_id
        aggregate_type = command.aggregate_type
        snapshot = command.snapshot

        # Trigger Celery task
        task = update_read_model_task.delay(
            command_id="",  # We'll need to handle this differently
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            snapshot=snapshot,
        )

        logger.info(f"Celery task triggered with task_id: {task.id}")
