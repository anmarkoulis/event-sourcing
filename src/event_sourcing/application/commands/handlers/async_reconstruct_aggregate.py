import logging

from event_sourcing.application.commands.aggregate import (
    AsyncReconstructAggregateCommand,
)
from event_sourcing.application.tasks.reconstruct_aggregate import (
    reconstruct_aggregate_task,
)

logger = logging.getLogger(__name__)


class AsyncReconstructAggregateCommandHandler:
    """Handler for asynchronously reconstructing aggregates via Celery"""

    def __init__(self) -> None:
        """Initialize the async handler (no dependencies needed as it just triggers Celery)"""

    async def handle(self, command: AsyncReconstructAggregateCommand) -> None:
        """Handle the async command by triggering a Celery task"""
        logger.info(
            f"Triggering Celery task for reconstruct aggregate command"
        )

        # Extract data from command
        aggregate_id = command.aggregate_id
        aggregate_type = command.aggregate_type
        entity_name = command.entity_name

        # Trigger Celery task
        try:
            task = reconstruct_aggregate_task.delay(
                command_id="",  # We'll need to handle this differently
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                entity_name=entity_name,
            )

            logger.info(f"Celery task triggered with task_id: {task.id}")
        except Exception as e:
            logger.error(f"Error triggering Celery task: {e}")
            raise e
