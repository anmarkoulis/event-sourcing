from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid


class DomainEvent(BaseModel):
    """Base domain event for all business events"""
    
    event_id: str
    aggregate_id: str
    aggregate_type: str  # "client", "project", etc.
    event_type: str      # "Created", "Updated", "Deleted"
    timestamp: datetime
    version: str
    data: Dict[str, Any]  # Generic event data
    metadata: Dict[str, Any]  # User, source, etc.
    validation_info: Optional[Dict[str, Any]] = None  # Validation metadata
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def create(cls, aggregate_id: str, aggregate_type: str, event_type: str, 
               data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> "DomainEvent":
        """Create a new domain event"""
        return cls(
            event_id=str(uuid.uuid4()),
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            data=data,
            metadata=metadata or {},
            validation_info={}
        ) 