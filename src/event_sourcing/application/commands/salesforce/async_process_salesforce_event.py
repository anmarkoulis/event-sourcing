from pydantic import BaseModel


class AsyncProcessSalesforceEventCommand(BaseModel):
    """Command to asynchronously process Salesforce CDC events via Celery"""

    raw_event: dict
    entity_name: str
    change_type: str
