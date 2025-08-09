import uuid
from unittest.mock import MagicMock

import pytest

from event_sourcing.application.commands.handlers.user.request_password_reset import (
    RequestPasswordResetCommandHandler,
)
from event_sourcing.application.commands.user.request_password_reset import (
    RequestPasswordResetCommand,
)


@pytest.fixture
def handler(
    event_store_mock: MagicMock,
    event_handler_mock: MagicMock,
    unit_of_work: MagicMock,
    snapshot_store_mock: MagicMock,
) -> RequestPasswordResetCommandHandler:
    return RequestPasswordResetCommandHandler(
        event_store=event_store_mock,
        snapshot_store=snapshot_store_mock,
        event_handler=event_handler_mock,
        unit_of_work=unit_of_work,
    )


@pytest.fixture
def request_password_reset_command() -> RequestPasswordResetCommand:
    return RequestPasswordResetCommand(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    )


class TestRequestPasswordResetCommandHandler:
    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: RequestPasswordResetCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        request_password_reset_command: RequestPasswordResetCommand,
    ) -> None:
        await handler.handle(request_password_reset_command)

        event_store_mock.get_stream.assert_awaited_once()
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()
        unit_of_work.rollback.assert_not_awaited()
