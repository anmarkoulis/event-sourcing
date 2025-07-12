import logging

from event_sourcing.application.commands.crm import AsyncProcessCRMEventCommand
from event_sourcing.application.events.event_handler import (
    EventHandlerInterface,
)

logger = logging.getLogger(__name__)


class AsyncProcessCRMEventCommandHandler:
    """Handler for asynchronously processing CRM events via event handler"""

    def __init__(self, event_handler: EventHandlerInterface):
        """
        Initialize the async handler with event handler dependency

        :param event_handler: The event handler to use for dispatching events
        """
        self.event_handler = event_handler

    async def handle(self, command: AsyncProcessCRMEventCommand) -> None:
        """Handle the async command by dispatching event via event handler"""
        logger.info(
            f"Dispatching {command.provider} CRM event via event handler"
        )

        # Use the event handler to dispatch the event
        try:
            await self.event_handler.dispatch(
                event=command.raw_event,
                delay=None,  # No delay for now
                queue=None,  # Use default queue
            )
            logger.info(
                f"Successfully dispatched {command.provider} CRM event"
            )
        except Exception as e:
            logger.error(f"Error dispatching event: {e}")
            raise e
