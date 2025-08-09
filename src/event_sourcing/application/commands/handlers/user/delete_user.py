import logging

from event_sourcing.application.commands.handlers.base import CommandHandler
from event_sourcing.application.commands.user.delete_user import (
    DeleteUserCommand,
)
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.unit_of_work import BaseUnitOfWork

logger = logging.getLogger(__name__)


class DeleteUserCommandHandler(CommandHandler[DeleteUserCommand]):
    """Handler for deleting users"""

    def __init__(
        self,
        event_store: EventStore,
        event_handler: EventHandler,
        unit_of_work: BaseUnitOfWork,
    ):
        self.event_store = event_store
        self.event_handler = event_handler
        self.unit_of_work = unit_of_work

    async def handle(self, command: DeleteUserCommand) -> None:
        logger.info(f"Deleting user: {command.user_id}")

        # Get existing events for the user
        events = await self.event_store.get_stream(
            command.user_id, AggregateTypeEnum.USER
        )

        # Reconstruct the aggregate from events
        user = UserAggregate(command.user_id)
        for event in events:
            user.apply(event)

        # Delete the user
        new_events = user.delete_user()

        async with self.unit_of_work:
            await self.event_store.append_to_stream(
                command.user_id,
                AggregateTypeEnum.USER,
                new_events,
            )
            await self.event_handler.dispatch(new_events)

        logger.info(f"Deleted user: {command.user_id}")
