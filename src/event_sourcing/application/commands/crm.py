from pydantic import BaseModel

from event_sourcing.dto.event import EventWriteDTO


class ProcessCRMEventCommand(BaseModel):
    """Generic command for processing CRM events from any provider"""

    raw_event: EventWriteDTO
    provider: str  # "salesforce", "hubspot", etc.
    entity_type: str  # "client", "deal", etc.


class AsyncProcessCRMEventCommand(BaseModel):
    """Generic command for asynchronously processing CRM events from any provider via Celery"""

    raw_event: EventWriteDTO
    provider: str  # "salesforce", "hubspot", etc.
    entity_type: str  # "client", "deal", etc.
