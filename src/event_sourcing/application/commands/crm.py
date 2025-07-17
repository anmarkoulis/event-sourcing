from typing import Any, Dict

from pydantic import BaseModel


class ProcessCRMEventCommand(BaseModel):
    """Generic command for processing CRM events from any provider"""

    provider: str  # "salesforce", "hubspot", etc.
    raw_event: Dict[str, Any]  # Raw CRM event from external system
