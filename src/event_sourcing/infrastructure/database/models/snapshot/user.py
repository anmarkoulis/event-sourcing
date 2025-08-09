from event_sourcing.infrastructure.database.models.snapshot.snapshot import (
    Snapshot,
)


class UserSnapshot(Snapshot):
    """Snapshot row for the User aggregate.

    The primary key `id` equals the aggregate_id.
    """
