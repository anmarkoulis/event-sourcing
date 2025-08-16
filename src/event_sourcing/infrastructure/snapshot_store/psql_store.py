"""PostgreSQL-based snapshot store implementation."""

import logging
from typing import Any, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from event_sourcing.domain.aggregates.base import Aggregate
from event_sourcing.infrastructure.database.models.write.snapshot import (
    UserSnapshot,
)
from event_sourcing.infrastructure.snapshot_store.base import SnapshotStore
from event_sourcing.infrastructure.snapshot_store.dto.base import SnapshotDTO

logger = logging.getLogger(__name__)

T_Agg = TypeVar("T_Agg", bound=Aggregate)


class PsqlSnapshotStore(SnapshotStore[T_Agg]):
    """PostgreSQL-based snapshot store implementation."""

    def __init__(self, session: Session) -> None:
        """Initialize PostgreSQL snapshot store.

        :param session: Database session.
        """
        self.session = session

    async def save_snapshot(
        self, aggregate_id: str, snapshot: SnapshotDTO[Any]
    ) -> None:
        """Save a snapshot to the database.

        :param aggregate_id: ID of the aggregate.
        :param snapshot: Snapshot DTO to save.
        """
        try:
            # Convert DTO to database model
            db_snapshot = UserSnapshot(
                aggregate_id=snapshot.aggregate_id,
                aggregate_type=snapshot.aggregate_type,
                data=snapshot.data,
                revision=snapshot.revision,
                created_at=snapshot.created_at,
                updated_at=snapshot.updated_at,
            )

            # Save to database
            self.session.add(db_snapshot)
            self.session.commit()

            logger.info(
                f"Saved snapshot for aggregate {aggregate_id} at revision {snapshot.revision}"
            )

        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
            self.session.rollback()
            raise

    async def get_snapshot(
        self, aggregate_id: str, aggregate_class: Type[T_Agg]
    ) -> Optional[SnapshotDTO[Any]]:
        """Get the latest snapshot for an aggregate.

        :param aggregate_id: ID of the aggregate.
        :param aggregate_class: Class of the aggregate.
        :return: Snapshot DTO if found, None otherwise.
        """
        try:
            # Query database for latest snapshot
            db_snapshot = (
                self.session.query(UserSnapshot)
                .filter(UserSnapshot.aggregate_id == aggregate_id)
                .order_by(UserSnapshot.revision.desc())
                .first()
            )

            if not db_snapshot:
                logger.info(f"No snapshot found for aggregate {aggregate_id}")
                return None

            # Convert database model to DTO
            snapshot_dto = SnapshotDTO[Any](
                aggregate_id=db_snapshot.aggregate_id,
                aggregate_type=db_snapshot.aggregate_type,
                data=db_snapshot.data,
                revision=db_snapshot.revision,
                created_at=db_snapshot.created_at,
                updated_at=db_snapshot.updated_at,
            )

            logger.info(
                f"Retrieved snapshot for aggregate {aggregate_id} at revision {db_snapshot.revision}"
            )

            return snapshot_dto

        except Exception as e:
            logger.error(f"Error retrieving snapshot: {e}")
            raise

    async def get_snapshot_at_revision(
        self, aggregate_id: str, revision: int
    ) -> Optional[SnapshotDTO[Any]]:
        """Get a snapshot at a specific revision.

        :param aggregate_id: ID of the aggregate.
        :param revision: Revision number.
        :return: Snapshot DTO if found, None otherwise.
        """
        try:
            # Query database for specific revision
            db_snapshot = (
                self.session.query(UserSnapshot)
                .filter(
                    UserSnapshot.aggregate_id == aggregate_id,
                    UserSnapshot.revision == revision,
                )
                .first()
            )

            if not db_snapshot:
                logger.info(
                    f"No snapshot found for aggregate {aggregate_id} at revision {revision}"
                )
                return None

            # Convert database model to DTO
            snapshot_dto = SnapshotDTO[Any](
                aggregate_id=db_snapshot.aggregate_id,
                aggregate_type=db_snapshot.aggregate_type,
                data=db_snapshot.data,
                revision=db_snapshot.revision,
                created_at=db_snapshot.created_at,
                updated_at=db_snapshot.updated_at,
            )

            logger.info(
                f"Retrieved snapshot for aggregate {aggregate_id} at revision {revision}"
            )

            return snapshot_dto

        except Exception as e:
            logger.error(f"Error retrieving snapshot at revision: {e}")
            raise

    async def delete_snapshots(self, aggregate_id: str) -> None:
        """Delete all snapshots for an aggregate.

        :param aggregate_id: ID of the aggregate.
        """
        try:
            # Delete all snapshots for the aggregate
            deleted_count = (
                self.session.query(UserSnapshot)
                .filter(UserSnapshot.aggregate_id == aggregate_id)
                .delete()
            )

            self.session.commit()

            logger.info(
                f"Deleted {deleted_count} snapshots for aggregate {aggregate_id}"
            )

        except Exception as e:
            logger.error(f"Error deleting snapshots: {e}")
            self.session.rollback()
            raise
