import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from event_sourcing.application.queries.handlers.user.get_user import (
    GetUserQueryHandler,
)
from event_sourcing.application.queries.user.get_user import GetUserQuery
from event_sourcing.dto.user import UserDTO
from event_sourcing.infrastructure.read_model import ReadModel


@pytest.fixture
def read_model_mock() -> MagicMock:
    rm = MagicMock(spec_set=ReadModel)
    rm.get_user = AsyncMock()
    return rm


@pytest.fixture
def handler(read_model_mock: MagicMock) -> GetUserQueryHandler:
    return GetUserQueryHandler(read_model=read_model_mock)


@pytest.fixture
def query() -> GetUserQuery:
    return GetUserQuery(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111")
    )


class TestGetUserQueryHandler:
    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: GetUserQueryHandler,
        read_model_mock: MagicMock,
        query: GetUserQuery,
    ) -> None:
        now = datetime.now(timezone.utc)
        expected = UserDTO(
            id=query.user_id,
            username="alice",
            email="a@example.com",
            first_name="A",
            last_name="B",
            created_at=now,
            updated_at=now,
        )
        read_model_mock.get_user.return_value = expected

        result = await handler.handle(query)

        read_model_mock.get_user.assert_awaited_once_with(str(query.user_id))
        assert result == expected

    @pytest.mark.asyncio
    async def test_handle_error_returns_none(
        self,
        handler: GetUserQueryHandler,
        read_model_mock: MagicMock,
        query: GetUserQuery,
    ) -> None:
        read_model_mock.get_user.side_effect = Exception("db error")

        result = await handler.handle(query)

        assert result is None
