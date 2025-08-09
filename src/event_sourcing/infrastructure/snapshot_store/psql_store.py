import uuid
from typing import Final, Mapping, Optional, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.dto.snapshot import SnapshotDTO
from event_sourcing.enums import AggregateTypeEnum
from event_sourcing.infrastructure.database.models.snapshot import (
    Snapshot,
    UserSnapshot,
)
from event_sourcing.infrastructure.snapshot_store.base import (
    SnapshotStore,
    T_Agg,
)


class PsqlSnapshotStore(SnapshotStore[T_Agg]):
    """Generic Postgres snapshot store that routes by aggregate type."""

    def __init__(self, session: AsyncSession):
        self.session = session

    _TABLES: Final[Mapping[AggregateTypeEnum, Type[Snapshot]]] = {
        AggregateTypeEnum.USER: UserSnapshot,
    }

    def _table_for(self, aggregate_type: AggregateTypeEnum) -> Type[Snapshot]:
        try:
            return self._TABLES[aggregate_type]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported aggregate type for snapshots: {aggregate_type}"
            ) from exc

    async def get(
        self, aggregate_id: uuid.UUID, aggregate_type: AggregateTypeEnum
    ) -> Optional[SnapshotDTO[T_Agg]]:
        table = self._table_for(aggregate_type)
        stmt = select(table).where(table.id == aggregate_id)
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None

        return SnapshotDTO(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            data=row.data,
            revision=row.revision,
            created_at=getattr(row, "created_at", None),
            updated_at=getattr(row, "updated_at", None),
        )

    async def set(self, dto: SnapshotDTO[T_Agg]) -> None:
        table = self._table_for(dto.aggregate_type)
        existing = await self.session.get(table, dto.aggregate_id)
        if existing is None:
            row = table(
                id=dto.aggregate_id, revision=dto.revision, data=dto.data
            )
            self.session.add(row)
        else:
            existing.revision = dto.revision
            existing.data = dto.data
