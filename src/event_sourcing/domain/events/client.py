from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from .base import DomainEvent


class ClientCreatedEvent(DomainEvent):
    """Client created event"""
    
    @classmethod
    def create(cls, client_id: str, data: Dict[str, Any], 
               metadata: Optional[Dict[str, Any]] = None) -> "ClientCreatedEvent":
        """Create a client created event"""
        return cls(
            event_id=str(uuid.uuid4()),
            aggregate_id=client_id,
            aggregate_type="client",
            event_type="Created",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            data=data,
            metadata=metadata or {},
            validation_info={}
        )


class ClientUpdatedEvent(DomainEvent):
    """Client updated event"""
    
    @classmethod
    def create(cls, client_id: str, data: Dict[str, Any], 
               metadata: Optional[Dict[str, Any]] = None) -> "ClientUpdatedEvent":
        """Create a client updated event"""
        return cls(
            event_id=str(uuid.uuid4()),
            aggregate_id=client_id,
            aggregate_type="client",
            event_type="Updated",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            data=data,
            metadata=metadata or {},
            validation_info={}
        )


class ClientDeletedEvent(DomainEvent):
    """Client deleted event"""
    
    @classmethod
    def create(cls, client_id: str, data: Dict[str, Any], 
               metadata: Optional[Dict[str, Any]] = None) -> "ClientDeletedEvent":
        """Create a client deleted event"""
        return cls(
            event_id=str(uuid.uuid4()),
            aggregate_id=client_id,
            aggregate_type="client",
            event_type="Deleted",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            data=data,
            metadata=metadata or {},
            validation_info={}
        ) 