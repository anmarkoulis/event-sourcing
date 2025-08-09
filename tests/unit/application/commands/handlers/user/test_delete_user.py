import uuid
from unittest.mock import MagicMock

import pytest

from event_sourcing.application.commands.handlers.user.delete_user import (
    DeleteUserCommandHandler,
)
from event_sourcing.application.commands.user.delete_user import (
    DeleteUserCommand,
)


@pytest.fixture
def handler(
    event_store_mock: MagicMock,
    event_handler_mock: MagicMock,
    unit_of_work: MagicMock,
    snapshot_store_mock: MagicMock,
) -> DeleteUserCommandHandler:
    return DeleteUserCommandHandler(
        event_store=event_store_mock,
        snapshot_store=snapshot_store_mock,
        event_handler=event_handler_mock,
        unit_of_work=unit_of_work,
    )


@pytest.fixture
def delete_user_command() -> DeleteUserCommand:
    return DeleteUserCommand(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    )


class TestDeleteUserCommandHandler:
    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: DeleteUserCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        delete_user_command: DeleteUserCommand,
    ) -> None:
        await handler.handle(delete_user_command)

        event_store_mock.get_stream.assert_awaited_once()
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()
        unit_of_work.rollback.assert_not_awaited()
