import logging

from event_sourcing.application.commands.salesforce import (
    AsyncProcessSalesforceEventCommand,
)

logger = logging.getLogger(__name__)


class AsyncProcessSalesforceEventCommandHandler:
    """Handler for asynchronously processing Salesforce events via Celery"""

    def __init__(self) -> None:
        """Initialize the async handler (no dependencies needed as it just triggers Celery)"""

    async def handle(
        self, command: AsyncProcessSalesforceEventCommand
    ) -> None:
        """Handle the async command by triggering a Celery task"""
        logger.info(f"Triggering Celery task for command")

        # Extract data from command
        raw_event = command.raw_event
        entity_name = command.entity_name
        change_type = command.change_type

        # Trigger Celery task using dynamic import
        try:
            from event_sourcing.application.tasks.process_salesforce_event import (
                process_salesforce_event_task,
            )

            task = process_salesforce_event_task.delay(
                command_id="",  # We'll need to handle this differently
                raw_event=raw_event,
                entity_name=entity_name,
                change_type=change_type,
            )
            logger.info(f"Celery task triggered with task_id: {task.id}")
        except Exception as e:
            logger.error(f"Error triggering Celery task: {e}")
            raise e
