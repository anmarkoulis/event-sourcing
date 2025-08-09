import uuid
from unittest.mock import MagicMock

import pytest

from event_sourcing.application.commands.handlers.user.update_user import (
    UpdateUserCommandHandler,
)
from event_sourcing.application.commands.user.update_user import (
    UpdateUserCommand,
)


@pytest.fixture
def handler(
    event_store_mock: MagicMock,
    event_handler_mock: MagicMock,
    unit_of_work: MagicMock,
    snapshot_store_mock: MagicMock,
) -> UpdateUserCommandHandler:
    return UpdateUserCommandHandler(
        event_store=event_store_mock,
        snapshot_store=snapshot_store_mock,
        event_handler=event_handler_mock,
        unit_of_work=unit_of_work,
    )


@pytest.fixture
def update_user_command() -> UpdateUserCommand:
    return UpdateUserCommand(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        first_name="New",
        last_name="Name",
        email="new@example.com",
    )


class TestUpdateUserCommandHandler:
    """Unit tests for UpdateUserCommandHandler"""

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: UpdateUserCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        update_user_command: UpdateUserCommand,
    ) -> None:
        await handler.handle(update_user_command)

        event_store_mock.get_stream.assert_awaited_once()
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()
        unit_of_work.rollback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_propagates_domain_error(
        self,
        handler: UpdateUserCommandHandler,
        event_store_mock: MagicMock,
        update_user_command: UpdateUserCommand,
    ) -> None:
        bad_command = UpdateUserCommand(
            user_id=update_user_command.user_id,
            first_name=None,
            last_name=None,
            email=None,
        )
        with pytest.raises(ValueError):
            await handler.handle(bad_command)
