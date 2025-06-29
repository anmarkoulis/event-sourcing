import uuid
from datetime import datetime
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel


class Command(BaseModel):
    """Base command for all write operations"""

    command_id: str
    command_type: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    # Class attribute for subclasses to define
    COMMAND_TYPE: ClassVar[Optional[str]] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Command":
        """Create a new command"""
        if cls.COMMAND_TYPE is None:
            raise ValueError(f"Class {cls.__name__} must define COMMAND_TYPE")

        return cls(
            command_id=str(uuid.uuid4()),
            command_type=cls.COMMAND_TYPE,
            timestamp=datetime.utcnow(),
            data=data,
            metadata=metadata or {},
        )
