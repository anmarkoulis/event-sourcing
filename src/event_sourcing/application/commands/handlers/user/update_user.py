import logging

from event_sourcing.application.commands.handlers.base import CommandHandler
from event_sourcing.application.commands.user.update_user import (
    UpdateUserCommand,
)
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.dto.snapshot import UserSnapshotDTO
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.snapshot_store.base import SnapshotStore
from event_sourcing.infrastructure.unit_of_work import BaseUnitOfWork

logger = logging.getLogger(__name__)


class UpdateUserCommandHandler(CommandHandler[UpdateUserCommand]):
    """Handler for updating users"""

    def __init__(
        self,
        event_store: EventStore,
        snapshot_store: SnapshotStore | None,
        event_handler: EventHandler,
        unit_of_work: BaseUnitOfWork,
    ):
        self.event_store = event_store
        self.snapshot_store = snapshot_store
        self.event_handler = event_handler
        self.unit_of_work = unit_of_work

    async def handle(self, command: UpdateUserCommand) -> None:
        logger.debug(f"Updating user: {command.user_id}")

        snapshot_dto = (
            await self.snapshot_store.get(
                command.user_id, AggregateTypeEnum.USER
            )
            if self.snapshot_store is not None
            else None
        )
        last_rev = snapshot_dto.revision if snapshot_dto else None

        events = await self.event_store.get_stream(
            command.user_id, AggregateTypeEnum.USER, start_revision=last_rev
        )

        user = (
            UserAggregate.from_snapshot(
                command.user_id, snapshot_dto.data, snapshot_dto.revision
            )
            if snapshot_dto
            else UserAggregate(command.user_id)
        )
        for event in events:
            if last_rev is not None and event.revision <= last_rev:
                continue
            user.apply(event)

        # Update the user with only the fields that are available
        new_events = user.update_user(
            email=command.email,
            first_name=command.first_name,
            last_name=command.last_name,
        )

        async with self.unit_of_work:
            await self.event_store.append_to_stream(
                command.user_id,
                AggregateTypeEnum.USER,
                new_events,
            )
            await self.event_handler.dispatch(new_events)

            if self.snapshot_store is not None:
                data, rev = user.to_snapshot()
                await self.snapshot_store.set(
                    UserSnapshotDTO(
                        aggregate_id=command.user_id,
                        data=data,
                        revision=rev,
                    )
                )

        logger.debug(f"Updated user: {command.user_id}")
