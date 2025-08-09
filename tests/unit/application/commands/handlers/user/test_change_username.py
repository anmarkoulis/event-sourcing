import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from event_sourcing.application.commands.handlers.user.change_username import (
    ChangeUsernameCommandHandler,
)
from event_sourcing.application.commands.user.change_username import (
    ChangeUsernameCommand,
)
from event_sourcing.dto.events.factory import EventFactory


@pytest.fixture
def handler(
    event_store_mock: MagicMock,
    event_handler_mock: MagicMock,
    unit_of_work: MagicMock,
    snapshot_store_mock: MagicMock,
) -> ChangeUsernameCommandHandler:
    return ChangeUsernameCommandHandler(
        event_store=event_store_mock,
        snapshot_store=snapshot_store_mock,
        event_handler=event_handler_mock,
        unit_of_work=unit_of_work,
    )


@pytest.fixture
def change_username_command() -> ChangeUsernameCommand:
    return ChangeUsernameCommand(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        new_username="new_name",
    )


class TestChangeUsernameCommandHandler:
    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: ChangeUsernameCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        change_username_command: ChangeUsernameCommand,
    ) -> None:
        # Seed prior state with USER_CREATED so old_username is not None
        seed_event = EventFactory.create_user_created(
            aggregate_id=change_username_command.user_id,
            username="old_name",
            email="user@example.com",
            first_name="",
            last_name="",
            password_hash="hash",  # noqa: S106 # pragma: allowlist secret
            revision=1,
        )
        event_store_mock.get_stream = AsyncMock(return_value=[seed_event])

        await handler.handle(change_username_command)

        event_store_mock.get_stream.assert_awaited_once()
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()
        unit_of_work.rollback.assert_not_awaited()
