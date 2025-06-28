import logging

from event_sourcing.application.commands.salesforce import (
    AsyncProcessSalesforceEventCommand,
)
from event_sourcing.application.tasks.process_salesforce_event import (
    process_salesforce_event_task,
)

logger = logging.getLogger(__name__)


class AsyncProcessSalesforceEventCommandHandler:
    """Handler for asynchronously processing Salesforce events via Celery"""

    def __init__(self):
        """Initialize the async handler (no dependencies needed as it just triggers Celery)"""

    async def handle(
        self, command: AsyncProcessSalesforceEventCommand
    ) -> None:
        """Handle the async command by triggering a Celery task"""
        logger.info(
            f"Triggering Celery task for command: {command.command_id}"
        )

        # Extract data from command
        raw_event = command.data["raw_event"]
        entity_name = command.data["entity_name"]
        change_type = command.data["change_type"]

        # Trigger Celery task
        try:
            task = process_salesforce_event_task.delay(
                command_id=command.command_id,
                raw_event=raw_event,
                entity_name=entity_name,
                change_type=change_type,
            )
            logger.info(
                f"Celery task triggered with task_id: {task.id} for command: {command.command_id}"
            )
        except Exception as e:
            logger.error(f"Error triggering Celery task: {e}")
            raise e
