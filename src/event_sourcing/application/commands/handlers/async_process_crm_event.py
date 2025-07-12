import logging

from event_sourcing.application.commands.crm import AsyncProcessCRMEventCommand

logger = logging.getLogger(__name__)


class AsyncProcessCRMEventCommandHandler:
    """Handler for asynchronously processing CRM events via Celery"""

    def __init__(self) -> None:
        """Initialize the async handler (no dependencies needed as it just triggers Celery)"""

    async def handle(self, command: AsyncProcessCRMEventCommand) -> None:
        """Handle the async command by triggering a Celery task"""
        logger.info(f"Triggering Celery task for {command.provider} CRM event")

        # Extract data from command
        raw_event = command.raw_event
        provider = command.provider
        entity_type = command.entity_type

        # Trigger Celery task using dynamic import
        try:
            from event_sourcing.application.tasks.process_crm_event import (
                process_crm_event_task,
            )

            task = process_crm_event_task.delay(
                command_id="",  # We'll need to handle this differently
                raw_event=raw_event,
                provider=provider,
                entity_type=entity_type,
            )
            logger.info(f"Celery task triggered with task_id: {task.id}")
        except Exception as e:
            logger.error(f"Error triggering Celery task: {e}")
            raise e
