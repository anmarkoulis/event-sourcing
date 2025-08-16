"""PostgreSQL-based user snapshot store implementation."""

from typing import Any

from event_sourcing.infrastructure.snapshot_store.dto.user import (
    UserSnapshotDTO,
)
from event_sourcing.infrastructure.snapshot_store.psql_store import (
    PsqlSnapshotStore,
)


class PsqlUserSnapshotStore(PsqlSnapshotStore):
    """PostgreSQL-based user snapshot store implementation."""

    def __init__(self, session: Any) -> None:
        """Initialize PostgreSQL user snapshot store.

        :param session: Database session.
        """
        super().__init__(session)

    async def save_user_snapshot(
        self, aggregate_id: str, snapshot: UserSnapshotDTO
    ) -> None:
        """Save a user snapshot to the database.

        :param aggregate_id: ID of the user aggregate.
        :param snapshot: User snapshot DTO to save.
        """
        await self.save_snapshot(aggregate_id, snapshot)

    async def get_user_snapshot(self, aggregate_id: str) -> UserSnapshotDTO:
        """Get the latest user snapshot.

        :param aggregate_id: ID of the user aggregate.
        :return: User snapshot DTO if found, None otherwise.
        """
        from event_sourcing.domain.aggregates.user import UserAggregate

        snapshot = await self.get_snapshot(aggregate_id, UserAggregate)
        if snapshot:
            return UserSnapshotDTO(**snapshot.dict())
        return None
