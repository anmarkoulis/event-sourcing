from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from .base import Command


class ProcessSalesforceEventCommandData(BaseModel):
    """Data for processing Salesforce events"""
    raw_event: dict  # Raw Salesforce CDC event
    entity_name: str
    change_type: str


class ProcessSalesforceEventCommand(Command):
    """Command to process Salesforce CDC events"""
    
    @classmethod
    def create(cls, raw_event: dict, entity_name: str, change_type: str,
               metadata: Optional[Dict[str, Any]] = None) -> "ProcessSalesforceEventCommand":
        """Create a process Salesforce event command"""
        data = ProcessSalesforceEventCommandData(
            raw_event=raw_event,
            entity_name=entity_name,
            change_type=change_type
        )
        return cls(
            command_id=str(uuid.uuid4()),
            command_type="ProcessSalesforceEvent",
            timestamp=datetime.utcnow(),
            data=data.dict(),
            metadata=metadata or {}
        )


class BackfillEntityTypeCommandData(BaseModel):
    """Data for backfilling entity types"""
    entity_name: str
    page: int = 1
    page_size: int = 50


class BackfillEntityTypeCommand(Command):
    """Command to backfill an entity type"""
    
    @classmethod
    def create(cls, entity_name: str, page: int = 1, page_size: int = 50,
               metadata: Optional[Dict[str, Any]] = None) -> "BackfillEntityTypeCommand":
        """Create a backfill entity type command"""
        data = BackfillEntityTypeCommandData(
            entity_name=entity_name,
            page=page,
            page_size=page_size
        )
        return cls(
            command_id=str(uuid.uuid4()),
            command_type="BackfillEntityType",
            timestamp=datetime.utcnow(),
            data=data.dict(),
            metadata=metadata or {}
        )


class CreateClientCommandData(BaseModel):
    """Data for creating a client"""
    client_id: str
    data: dict
    source: str = "salesforce"  # "salesforce" or "backfill"


class CreateClientCommand(Command):
    """Command to create a client"""
    
    @classmethod
    def create(cls, client_id: str, data: dict, source: str = "salesforce",
               metadata: Optional[Dict[str, Any]] = None) -> "CreateClientCommand":
        """Create a create client command"""
        command_data = CreateClientCommandData(
            client_id=client_id,
            data=data,
            source=source
        )
        return cls(
            command_id=str(uuid.uuid4()),
            command_type="CreateClient",
            timestamp=datetime.utcnow(),
            data=command_data.dict(),
            metadata=metadata or {}
        ) 