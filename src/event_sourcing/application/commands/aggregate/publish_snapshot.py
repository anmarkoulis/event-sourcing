from typing import Any, Dict

from pydantic import BaseModel


class PublishSnapshotCommand(BaseModel):
    """Command to publish aggregate snapshot to external systems"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]
    event_type: str
