from typing import Any, Dict

from pydantic import BaseModel


class AsyncPublishSnapshotCommand(BaseModel):
    """Command to asynchronously publish aggregate snapshot to external systems via Celery"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]
    event_type: str
