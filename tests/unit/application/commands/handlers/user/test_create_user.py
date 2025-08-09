import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from event_sourcing.application.commands.handlers.user.create_user import (
    CreateUserCommandHandler,
)
from event_sourcing.application.commands.user.create_user import (
    CreateUserCommand,
)
from event_sourcing.application.events.handlers.base import EventHandler
from event_sourcing.enums import AggregateTypeEnum, EventType
from event_sourcing.infrastructure.event_store import EventStore
from event_sourcing.infrastructure.unit_of_work.base import BaseUnitOfWork


@pytest.fixture
def event_store_mock() -> MagicMock:
    store = MagicMock(spec=EventStore)
    store.search_events = AsyncMock(return_value=[])
    store.append_to_stream = AsyncMock()
    return store


@pytest.fixture
def event_handler_mock() -> MagicMock:
    handler = MagicMock(spec=EventHandler)
    handler.dispatch = AsyncMock()
    return handler


@pytest.fixture
def unit_of_work() -> MagicMock:
    """Mocked UnitOfWork that supports async context management and tracks state."""
    uow = MagicMock(spec=BaseUnitOfWork)

    # Track state
    uow.committed = False
    uow.rolled_back = False

    # Implement commit / rollback behavior
    async def _commit() -> None:
        uow.committed = True

    async def _rollback() -> None:
        uow.rolled_back = True

    uow.commit = AsyncMock(side_effect=_commit)
    uow.rollback = AsyncMock(side_effect=_rollback)

    # Implement async context manager behavior mirroring BaseUnitOfWork.__aexit__
    async def _aenter():  # type: ignore[no-untyped-def]
        return uow

    async def _aexit(exc_type, exc, tb):  # type: ignore[no-untyped-def]
        if exc:
            await uow.rollback()
        else:
            await uow.commit()
        return None

    uow.__aenter__ = AsyncMock(side_effect=_aenter)
    uow.__aexit__ = AsyncMock(side_effect=_aexit)

    return uow


@pytest.fixture
def handler(
    event_store_mock: MagicMock,
    event_handler_mock: MagicMock,
    unit_of_work: MagicMock,
    snapshot_store_mock: MagicMock,
) -> CreateUserCommandHandler:
    return CreateUserCommandHandler(
        event_store=event_store_mock,
        snapshot_store=snapshot_store_mock,
        event_handler=event_handler_mock,
        unit_of_work=unit_of_work,
    )


@pytest.fixture
def create_user_command() -> CreateUserCommand:
    return CreateUserCommand(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        username="newuser",
        email="newuser@example.com",
        first_name="New",
        last_name="User",
        password_hash="hashed",  # noqa: S106 # pragma: allowlist secret
    )


class TestCreateUserCommandHandler:
    """Unit tests for CreateUserCommandHandler"""

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: CreateUserCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        create_user_command: CreateUserCommand,
    ) -> None:
        await handler.handle(create_user_command)

        # append_to_stream is called once with correct aggregate type and events
        event_store_mock.append_to_stream.assert_awaited_once()
        agg_id, agg_type, events = (
            event_store_mock.append_to_stream.call_args.args
        )
        assert agg_type == AggregateTypeEnum.USER
        assert isinstance(events, list) and len(events) == 1
        assert events[0].event_type in {
            EventType.USER_CREATED,
            "USER_CREATED",
        }

        # events dispatched
        event_handler_mock.dispatch.assert_awaited_once()
        dispatched_events = event_handler_mock.dispatch.call_args.args[0]
        assert dispatched_events == events

        # UoW committed
        assert unit_of_work.committed is True
        assert unit_of_work.rolled_back is False

    @pytest.mark.asyncio
    async def test_handle_fails_when_username_already_exists(
        self,
        handler: CreateUserCommandHandler,
        event_store_mock: MagicMock,
        create_user_command: CreateUserCommand,
    ) -> None:
        event_store_mock.search_events = AsyncMock(
            side_effect=[
                [SimpleNamespace(event_type="USER_CREATED")],
                [],
            ]
        )

        with pytest.raises(ValueError):
            await handler.handle(create_user_command)

        event_store_mock.append_to_stream.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_fails_when_email_already_exists(
        self,
        handler: CreateUserCommandHandler,
        event_store_mock: MagicMock,
        create_user_command: CreateUserCommand,
    ) -> None:
        event_store_mock.search_events = AsyncMock(
            side_effect=[
                [],  # username unique
                [SimpleNamespace(event_type="USER_CREATED")],  # email dup
            ]
        )

        with pytest.raises(ValueError):
            await handler.handle(create_user_command)

        event_store_mock.append_to_stream.assert_not_called()
