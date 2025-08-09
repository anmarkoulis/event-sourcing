import logging

from event_sourcing.application.commands.handlers.base import CommandHandler
from event_sourcing.application.commands.user.change_password import (
    ChangePasswordCommand,
)
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.dto.snapshot import UserSnapshotDTO
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.snapshot_store.base import SnapshotStore
from event_sourcing.infrastructure.unit_of_work import BaseUnitOfWork

logger = logging.getLogger(__name__)


class ChangePasswordCommandHandler(CommandHandler[ChangePasswordCommand]):
    """Handler for changing passwords"""

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

    async def handle(self, command: ChangePasswordCommand) -> None:
        logger.info(f"Changing password for user: {command.user_id}")

        # Try snapshot (read-only); example assumes you have a snapshot store
        # injected elsewhere. For now, we keep logic ready for start_revision.
        snapshot_dto = (
            await self.snapshot_store.get(
                command.user_id, AggregateTypeEnum.USER
            )
            if self.snapshot_store is not None
            else None
        )
        last_rev = snapshot_dto.revision if snapshot_dto else None
        logger.debug(f"Last revision: {last_rev}")

        events = await self.event_store.get_stream(
            command.user_id, AggregateTypeEnum.USER, start_revision=last_rev
        )
        logger.debug(f"Events: {events}")

        user = (
            UserAggregate.from_snapshot(
                command.user_id, snapshot_dto.data, snapshot_dto.revision
            )
            if snapshot_dto
            else UserAggregate(command.user_id)
        )
        logger.debug(f"User: {user}")
        for event in events:
            # if last_rev is None, this applies all events
            # logger.debug(f"Event: {event.revision}")
            if last_rev is not None and event.revision <= last_rev:
                # logger.debug(f"Skipping event: {event.revision}")
                continue
            user.apply(event)

        # Change the password
        new_events = user.change_password(command.new_password_hash)
        logger.debug(f"New events: {new_events}")

        async with self.unit_of_work:
            await self.event_store.append_to_stream(
                command.user_id,
                AggregateTypeEnum.USER,
                new_events,
            )
            await self.event_handler.dispatch(new_events)
            # Optional: write snapshot after transaction success
            if self.snapshot_store is not None:
                logger.debug(f"Writing snapshot")
                data, rev = user.to_snapshot()
                logger.debug(f"Data: {data}")
                logger.debug(f"Revision: {rev}")
                await self.snapshot_store.set(
                    UserSnapshotDTO(
                        aggregate_id=command.user_id,
                        data=data,
                        revision=rev,
                    )
                )

        logger.info(f"Changed password for user: {command.user_id}")
