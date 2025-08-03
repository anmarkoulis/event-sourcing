import logging

from event_sourcing.application.commands.handlers.base import CommandHandler
from event_sourcing.application.commands.user import CreateUserCommand
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.unit_of_work import BaseUnitOfWork

logger = logging.getLogger(__name__)


class CreateUserCommandHandler(CommandHandler[CreateUserCommand]):
    """Handler for creating users"""

    def __init__(
        self,
        event_store: EventStore,
        event_handler: EventHandler,
        unit_of_work: BaseUnitOfWork,
    ):
        self.event_store = event_store
        self.event_handler = event_handler
        self.unit_of_work = unit_of_work

    async def handle(self, command: CreateUserCommand) -> None:
        logger.info(f"Creating user: {command.username}")
        user = UserAggregate(command.user_id)
        logger.info(f"User: {user}")

        new_events = user.create_user(
            username=command.username,
            email=command.email,
            first_name=command.first_name,
            last_name=command.last_name,
            password_hash=command.password_hash,
        )
        logger.info(f"New events: {new_events}")

        async with self.unit_of_work as uow:
            await self.event_store.append_to_stream(
                command.user_id, new_events, session=uow.db
            )
            await self.event_handler.dispatch(new_events)

        logger.info(f"Created user: {command.username}")
