import uuid
from unittest.mock import MagicMock

import pytest

from event_sourcing.application.commands.handlers.user.change_password import (
    ChangePasswordCommandHandler,
)
from event_sourcing.application.commands.user.change_password import (
    ChangePasswordCommand,
)
from event_sourcing.enums import AggregateTypeEnum


@pytest.fixture
def handler(
    event_store_mock: MagicMock,
    event_handler_mock: MagicMock,
    unit_of_work: MagicMock,
) -> ChangePasswordCommandHandler:
    return ChangePasswordCommandHandler(
        event_store=event_store_mock,
        event_handler=event_handler_mock,
        unit_of_work=unit_of_work,
    )


@pytest.fixture
def change_password_command() -> ChangePasswordCommand:
    return ChangePasswordCommand(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        new_password_hash="newhash",  # noqa: S106 # pragma: allowlist secret
    )


class TestChangePasswordCommandHandler:
    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: ChangePasswordCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        change_password_command: ChangePasswordCommand,
    ) -> None:
        await handler.handle(change_password_command)

        event_store_mock.get_stream.assert_awaited_once_with(
            change_password_command.user_id, AggregateTypeEnum.USER
        )
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()
        unit_of_work.rollback.assert_not_awaited()
