import logging

from event_sourcing.application.commands.handlers.base import CommandHandler
from event_sourcing.application.commands.user import CreateUserCommand
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.infrastructure.event_store import EventStore

logger = logging.getLogger(__name__)


class CreateUserCommandHandler(CommandHandler[CreateUserCommand]):
    """Handler for creating users"""

    def __init__(self, event_store: EventStore, event_handler: EventHandler):
        self.event_store = event_store
        self.event_handler = event_handler

    async def handle(self, command: CreateUserCommand) -> None:
        """Handle create user command"""
        # Create empty aggregate
        logger.info(f"Creating user: {command.username}")
        user = UserAggregate(command.user_id)
        logger.info(f"User: {user}")

        # Call domain method and get new events
        new_events = user.create_user(
            username=command.username,
            email=command.email,
            first_name=command.first_name,
            last_name=command.last_name,
            password_hash=command.password_hash,
        )
        logger.info(f"New events: {new_events}")

        # Store events and dispatch
        await self.event_store.append_to_stream(command.user_id, new_events)
        await self.event_handler.dispatch(new_events)

        logger.info(f"Created user: {command.username}")
