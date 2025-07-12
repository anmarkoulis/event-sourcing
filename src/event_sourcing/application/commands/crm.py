from typing import Any, Dict

from pydantic import BaseModel


class ProcessCRMEventCommand(BaseModel):
    """Generic command for processing CRM events from any provider"""

    raw_event: Dict[str, Any]
    provider: str  # "salesforce", "hubspot", etc.
    entity_type: str  # "client", "deal", etc.


class AsyncProcessCRMEventCommand(BaseModel):
    """Generic command for asynchronously processing CRM events from any provider via Celery"""

    raw_event: Dict[str, Any]
    provider: str  # "salesforce", "hubspot", etc.
    entity_type: str  # "client", "deal", etc.
