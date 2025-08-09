import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.infrastructure.database.models.snapshot import UserSnapshot
from event_sourcing.infrastructure.snapshot_store.base import SnapshotStore


class PsqlUserSnapshotStore(SnapshotStore):
    """Postgres-backed snapshot store for User aggregate (read-only).

    This expects `UserSnapshot.data` to be a JSON serialization of
    `UserAggregate` state. For now, we'll deserialize minimally.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(
        self, aggregate_id: uuid.UUID, aggregate_type: AggregateTypeEnum
    ) -> Optional[object]:
        if aggregate_type != AggregateTypeEnum.USER:
            return None

        stmt = select(UserSnapshot).where(UserSnapshot.id == aggregate_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None

        # Rebuild a minimal aggregate from snapshot data
        agg = UserAggregate(aggregate_id)
        data = row.data or {}
        # Best-effort field mapping (depends on your snapshot format)
        agg.username = data.get("username")
        agg.email = data.get("email")
        agg.first_name = data.get("first_name")
        agg.last_name = data.get("last_name")
        agg.password_hash = data.get("password_hash")
        agg.created_at = data.get("created_at")
        agg.updated_at = data.get("updated_at")
        agg.deleted_at = data.get("deleted_at")

        class _UserSnapshotObj:
            def __init__(
                self, aggregate: UserAggregate, revision: int
            ) -> None:
                self.aggregate = aggregate
                self.last_revision = revision

        return _UserSnapshotObj(agg, row.revision)

    async def set(
        self,
        aggregate_id: uuid.UUID,
        aggregate_type: AggregateTypeEnum,
        revision: int,
        data: dict,
    ) -> None:
        if aggregate_type != AggregateTypeEnum.USER:
            return

        existing = await self.session.get(UserSnapshot, aggregate_id)
        if existing is None:
            row = UserSnapshot(id=aggregate_id, revision=revision, data=data)
            self.session.add(row)
        else:
            existing.revision = revision
            existing.data = data
