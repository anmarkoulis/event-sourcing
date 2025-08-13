import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from event_sourcing.application.queries.handlers.user.get_user_history import (
    GetUserHistoryQueryHandler,
)
from event_sourcing.application.queries.user.get_user_history import (
    GetUserHistoryQuery,
)
from event_sourcing.dto.events.factory import EventFactory
from event_sourcing.dto.user import UserDTO
from event_sourcing.enums import AggregateTypeEnum


@pytest.fixture
def handler(event_store_mock: MagicMock) -> GetUserHistoryQueryHandler:
    # Configure the mock for this specific test
    event_store_mock.get_stream = AsyncMock()
    return GetUserHistoryQueryHandler(event_store=event_store_mock)


@pytest.fixture
def query() -> GetUserHistoryQuery:
    return GetUserHistoryQuery(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        timestamp=datetime.now(timezone.utc),
    )


class TestGetUserHistoryQueryHandler:
    @pytest.mark.asyncio
    async def test_handle_success_reconstructs_user(
        self,
        handler: GetUserHistoryQueryHandler,
        event_store_mock: MagicMock,
        query: GetUserHistoryQuery,
    ) -> None:
        # Seed minimal history: USER_CREATED
        created_event = EventFactory.create_user_created(
            aggregate_id=query.user_id,
            username="alice",
            email="a@example.com",
            first_name="A",
            last_name="B",
            password_hash="p",  # noqa: S106
            revision=1,
        )
        event_store_mock.get_stream.return_value = [created_event]

        result = await handler.handle(query)

        event_store_mock.get_stream.assert_awaited_once_with(
            query.user_id, AggregateTypeEnum.USER, end_time=query.timestamp
        )
        assert isinstance(result, UserDTO)
        assert result.username == "alice"
        assert result.email == "a@example.com"

    @pytest.mark.asyncio
    async def test_handle_no_events_returns_none(
        self,
        handler: GetUserHistoryQueryHandler,
        event_store_mock: MagicMock,
        query: GetUserHistoryQuery,
    ) -> None:
        event_store_mock.get_stream.return_value = []

        result = await handler.handle(query)

        assert result is None
