from typing import Any, ClassVar, Dict, Optional, cast

from pydantic import BaseModel

from .base import Command


class ProcessSalesforceEventCommandData(BaseModel):
    """Data for processing Salesforce events"""

    raw_event: dict  # Raw Salesforce CDC event
    entity_name: str
    change_type: str


class ProcessSalesforceEventCommand(Command):
    """Command to process Salesforce CDC events"""

    COMMAND_TYPE: ClassVar[str] = "ProcessSalesforceEvent"

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ProcessSalesforceEventCommand":
        """Create a process Salesforce event command"""
        return cast(
            "ProcessSalesforceEventCommand",
            super().create(data=data, metadata=metadata),
        )


class AsyncProcessSalesforceEventCommandData(BaseModel):
    """Data for asynchronously processing Salesforce events"""

    raw_event: dict  # Raw Salesforce CDC event
    entity_name: str
    change_type: str


class AsyncProcessSalesforceEventCommand(Command):
    """Command to asynchronously process Salesforce CDC events via Celery"""

    COMMAND_TYPE: ClassVar[str] = "AsyncProcessSalesforceEvent"

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AsyncProcessSalesforceEventCommand":
        """Create an async process Salesforce event command"""
        return cast(
            "AsyncProcessSalesforceEventCommand",
            super().create(data=data, metadata=metadata),
        )


class BackfillEntityTypeCommandData(BaseModel):
    """Data for backfilling entity types"""

    entity_name: str
    page: int = 1
    page_size: int = 50


class BackfillEntityTypeCommand(Command):
    """Command to backfill an entity type"""

    COMMAND_TYPE: ClassVar[str] = "BackfillEntityType"

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "BackfillEntityTypeCommand":
        """Create a backfill entity type command"""
        return cast(
            "BackfillEntityTypeCommand",
            super().create(data=data, metadata=metadata),
        )


class CreateClientCommandData(BaseModel):
    """Data for creating a client"""

    client_id: str
    data: dict
    source: str = "salesforce"  # "salesforce" or "backfill"


class CreateClientCommand(Command):
    """Command to create a client"""

    COMMAND_TYPE: ClassVar[str] = "CreateClient"

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "CreateClientCommand":
        """Create a create client command"""
        return cast(
            "CreateClientCommand", super().create(data=data, metadata=metadata)
        )
