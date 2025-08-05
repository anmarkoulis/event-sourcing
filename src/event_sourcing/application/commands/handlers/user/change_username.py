import logging
import uuid

from event_sourcing.application.commands.handlers.base import CommandHandler
from event_sourcing.application.commands.user import ChangeUsernameCommand
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.unit_of_work import BaseUnitOfWork

logger = logging.getLogger(__name__)


class ChangeUsernameCommandHandler(CommandHandler[ChangeUsernameCommand]):
    """Handler for changing usernames"""

    def __init__(
        self,
        event_store: EventStore,
        event_handler: EventHandler,
        unit_of_work: BaseUnitOfWork,
    ):
        self.event_store = event_store
        self.event_handler = event_handler
        self.unit_of_work = unit_of_work

    async def _validate_username_uniqueness(self, username: str) -> bool:
        """Validate that username is unique across all users"""
        try:
            # Search for existing users with this username
            existing_events = await self.event_store.search_events(
                aggregate_type=AggregateTypeEnum.USER,
                query_params={"username": username},
            )

            # If we find any USER_CREATED events with this username, it's not unique
            for event in existing_events:
                if event.event_type == "USER_CREATED":
                    logger.info(f"Username {username} already exists")
                    return False

            logger.info(f"Username {username} is unique")
            return True

        except Exception as e:
            logger.error(f"Error validating username uniqueness: {e}")
            # In case of error, we'll be conservative and assume it's not unique
            return False

    async def handle(self, command: ChangeUsernameCommand) -> None:
        # Generate unique execution ID to track if this handler is called multiple times
        execution_id = str(uuid.uuid4())
        logger.info(
            f"[{execution_id}] Starting username change for user: {command.user_id}"
        )

        # Validate uniqueness before changing the username
        if not await self._validate_username_uniqueness(command.new_username):
            raise ValueError("Username already exists")

        # Get existing events for the user
        events = await self.event_store.get_stream(
            command.user_id, AggregateTypeEnum.USER
        )
        logger.info(
            f"[{execution_id}] Retrieved {len(events)} existing events"
        )

        # Reconstruct the aggregate from events
        user = UserAggregate(command.user_id)
        for event in events:
            user.apply(event)

        # Change the username
        new_events = user.change_username(command.new_username)
        logger.info(
            f"[{execution_id}] Generated {len(new_events)} new events for username change"
        )

        for i, event in enumerate(new_events):
            logger.info(
                f"[{execution_id}] Event {i}: ID={event.event_id}, Type={event.event_type}, Revision={event.revision}, Object ID={id(event)}"
            )

        # Check if any of the new events already exist in the stream
        existing_event_ids = {e.event_id for e in events}
        events_to_append = []
        for event in new_events:
            if event.event_id in existing_event_ids:
                logger.warning(
                    f"[{execution_id}] Event {event.event_id} already exists in stream, skipping"
                )
            else:
                events_to_append.append(event)

        if not events_to_append:
            logger.info(f"[{execution_id}] No new events to append")
            return

        async with self.unit_of_work as uow:
            logger.info(
                f"[{execution_id}] Appending {len(events_to_append)} events to stream for user: {command.user_id}"
            )

            await self.event_store.append_to_stream(
                command.user_id,
                AggregateTypeEnum.USER,
                events_to_append,
                session=uow.db,
            )
            logger.info(
                f"[{execution_id}] Dispatching events to event handler"
            )
            await self.event_handler.dispatch(events_to_append)

        logger.info(
            f"[{execution_id}] Successfully changed username for user: {command.user_id}"
        )
