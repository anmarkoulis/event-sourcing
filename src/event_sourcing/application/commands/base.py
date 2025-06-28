import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class Command(BaseModel):
    """Base command for all write operations"""

    command_id: str
    command_type: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    @classmethod
    def create(
        cls,
        command_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Command":
        """Create a new command"""
        return cls(
            command_id=str(uuid.uuid4()),
            command_type=command_type,
            timestamp=datetime.utcnow(),
            data=data,
            metadata=metadata or {},
        )
