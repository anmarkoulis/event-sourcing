from pydantic import BaseModel


class ProcessSalesforceEventCommand(BaseModel):
    """Command to process Salesforce CDC events"""

    raw_event: dict
    entity_name: str
    change_type: str
