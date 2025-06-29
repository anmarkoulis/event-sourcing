from pydantic import BaseModel


class CreateClientCommand(BaseModel):
    """Command to create a client"""

    client_id: str
    data: dict
    source: str = "salesforce"
