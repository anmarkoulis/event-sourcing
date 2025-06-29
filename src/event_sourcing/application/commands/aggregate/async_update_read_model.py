from typing import Any, Dict

from pydantic import BaseModel


class AsyncUpdateReadModelCommand(BaseModel):
    """Command to asynchronously update read model with aggregate snapshot via Celery"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]
