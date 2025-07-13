from pydantic import BaseModel

from event_sourcing.dto.event import EventDTO


class ProcessCRMEventCommand(BaseModel):
    """Generic command for processing CRM events from any provider"""

    event: EventDTO
    provider: str  # "salesforce", "hubspot", etc.
