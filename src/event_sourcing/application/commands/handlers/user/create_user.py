import logging

from event_sourcing.application.commands.handlers.base import CommandHandler
from event_sourcing.application.commands.user.create_user import (
    CreateUserCommand,
)
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.dto.snapshot import UserSnapshotDTO
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.snapshot_store.base import SnapshotStore
from event_sourcing.infrastructure.unit_of_work import BaseUnitOfWork

logger = logging.getLogger(__name__)


class CreateUserCommandHandler(CommandHandler[CreateUserCommand]):
    """Handler for creating users"""

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

    async def _validate_username_uniqueness(self, username: str) -> bool:
        """Validate that username is unique across all users"""
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

    async def _validate_email_uniqueness(self, email: str) -> bool:
        """Validate that email is unique across all users"""
        # Search for existing users with this email
        existing_events = await self.event_store.search_events(
            aggregate_type=AggregateTypeEnum.USER,
            query_params={"email": email},
        )

        # If we find any USER_CREATED events with this email, it's not unique
        for event in existing_events:
            if event.event_type == "USER_CREATED":
                logger.info(f"Email {email} already exists")
                return False

        logger.info(f"Email {email} is unique")
        return True

    async def handle(self, command: CreateUserCommand) -> None:
        logger.info(f"Creating user: {command.username}")

        # Validate uniqueness before creating the user
        if not await self._validate_username_uniqueness(command.username):
            raise ValueError("Username already exists")

        if not await self._validate_email_uniqueness(command.email):
            raise ValueError("Email already exists")

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

        logger.info(f"Created user: {command.username}")
