import logging

from event_sourcing.application.commands.handlers.base import CommandHandler
from event_sourcing.application.commands.user import UpdateUserCommand
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.infrastructure.event_store import EventStore

logger = logging.getLogger(__name__)


class UpdateUserCommandHandler(CommandHandler[UpdateUserCommand]):
    """Handler for updating users"""

    def __init__(self, event_store: EventStore, event_handler: EventHandler):
        self.event_store = event_store
        self.event_handler = event_handler

    async def handle(self, command: UpdateUserCommand) -> None:
        """Handle update user command"""
        # Get all events for this aggregate
        events = await self.event_store.get_stream(command.user_id)

        # Create aggregate and replay events
        user = UserAggregate(command.user_id)
        for event in events:
            user.apply(event)

        # Call domain method and get new events
        new_events = user.update_user(
            first_name=command.first_name,
            last_name=command.last_name,
            email=command.email,
        )

        # Store events and dispatch
        await self.event_store.append_to_stream(command.user_id, new_events)
        await self.event_handler.dispatch(new_events)

        logger.info(f"Updated user: {command.user_id}")
