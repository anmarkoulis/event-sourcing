import uuid
from unittest.mock import MagicMock

import pytest

from event_sourcing.application.commands.handlers.user.complete_password_reset import (
    CompletePasswordResetCommandHandler,
)
from event_sourcing.application.commands.user.complete_password_reset import (
    CompletePasswordResetCommand,
)


@pytest.fixture
def handler(
    event_store_mock: MagicMock,
    event_handler_mock: MagicMock,
    unit_of_work: MagicMock,
    snapshot_store_mock: MagicMock,
) -> CompletePasswordResetCommandHandler:
    return CompletePasswordResetCommandHandler(
        event_store=event_store_mock,
        snapshot_store=snapshot_store_mock,
        event_handler=event_handler_mock,
        unit_of_work=unit_of_work,
    )


@pytest.fixture
def complete_password_reset_command() -> CompletePasswordResetCommand:
    return CompletePasswordResetCommand(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        new_password_hash="newhash",  # noqa: S106 # pragma: allowlist secret
        reset_token="token",  # noqa: S106
    )


class TestCompletePasswordResetCommandHandler:
    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: CompletePasswordResetCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        complete_password_reset_command: CompletePasswordResetCommand,
    ) -> None:
        await handler.handle(complete_password_reset_command)

        event_store_mock.get_stream.assert_awaited_once()
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()
        unit_of_work.rollback.assert_not_awaited()
