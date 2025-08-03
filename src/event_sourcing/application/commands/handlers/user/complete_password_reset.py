import logging

from event_sourcing.application.commands.handlers.base import CommandHandler
from event_sourcing.application.commands.user import (
    CompletePasswordResetCommand,
)
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.infrastructure.event_store import EventStore

logger = logging.getLogger(__name__)


class CompletePasswordResetCommandHandler(
    CommandHandler[CompletePasswordResetCommand]
):
    """Handler for completing password resets"""

    def __init__(self, event_store: EventStore, event_handler: EventHandler):
        self.event_store = event_store
        self.event_handler = event_handler

    async def handle(self, command: CompletePasswordResetCommand) -> None:
        """Handle complete password reset command"""
        # Get all events for this aggregate
        events = await self.event_store.get_stream(command.user_id)

        # Create aggregate and replay events
        user = UserAggregate(command.user_id)
        for event in events:
            user.apply(event)

        # Call domain method and get new events
        new_events = user.complete_password_reset(
            command.new_password_hash, command.reset_token
        )

        # Store events and dispatch
        await self.event_store.append_to_stream(command.user_id, new_events)
        await self.event_handler.dispatch(new_events)

        logger.info(f"Completed password reset for user: {command.user_id}")
