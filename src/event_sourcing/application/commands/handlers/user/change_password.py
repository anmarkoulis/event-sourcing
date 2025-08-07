import logging

from event_sourcing.application.commands.handlers.base import CommandHandler
from event_sourcing.application.commands.user.change_password import (
    ChangePasswordCommand,
)
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.unit_of_work import BaseUnitOfWork

logger = logging.getLogger(__name__)


class ChangePasswordCommandHandler(CommandHandler[ChangePasswordCommand]):
    """Handler for changing passwords"""

    def __init__(
        self,
        event_store: EventStore,
        event_handler: EventHandler,
        unit_of_work: BaseUnitOfWork,
    ):
        self.event_store = event_store
        self.event_handler = event_handler
        self.unit_of_work = unit_of_work

    async def handle(self, command: ChangePasswordCommand) -> None:
        logger.info(f"Changing password for user: {command.user_id}")

        # Get existing events for the user
        events = await self.event_store.get_stream(
            command.user_id, AggregateTypeEnum.USER
        )

        # Reconstruct the aggregate from events
        user = UserAggregate(command.user_id)
        for event in events:
            user.apply(event)

        # Change the password
        new_events = user.change_password(command.new_password_hash)

        async with self.unit_of_work as uow:
            await self.event_store.append_to_stream(
                command.user_id,
                AggregateTypeEnum.USER,
                new_events,
                session=uow.db,
            )
            await self.event_handler.dispatch(new_events)

        logger.info(f"Changed password for user: {command.user_id}")
