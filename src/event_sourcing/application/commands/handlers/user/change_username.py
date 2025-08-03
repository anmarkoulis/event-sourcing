import logging

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
        logger.info(f"Changing username for user: {command.user_id}")

        # Validate uniqueness before changing the username
        if not await self._validate_username_uniqueness(command.new_username):
            raise ValueError("Username already exists")

        # Get existing events for the user
        events = await self.event_store.get_stream(
            command.user_id, AggregateTypeEnum.USER
        )

        # Reconstruct the aggregate from events
        user = UserAggregate(command.user_id)
        for event in events:
            user.apply(event)

        # Change the username
        new_events = user.change_username(command.new_username)
        logger.info(f"New events: {new_events}")

        async with self.unit_of_work as uow:
            await self.event_store.append_to_stream(
                command.user_id,
                AggregateTypeEnum.USER,
                new_events,
                session=uow.db,
            )
            await self.event_handler.dispatch(new_events)

        logger.info(f"Changed username for user: {command.user_id}")
