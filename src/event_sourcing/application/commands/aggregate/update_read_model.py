from typing import Any, Dict

from pydantic import BaseModel


class UpdateReadModelCommand(BaseModel):
    """Command to update read model with aggregate snapshot"""

    aggregate_id: str
    aggregate_type: str
    snapshot: Dict[str, Any]
