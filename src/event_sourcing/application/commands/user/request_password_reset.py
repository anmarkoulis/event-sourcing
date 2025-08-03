import uuid

from pydantic import BaseModel


class RequestPasswordResetCommand(BaseModel):
    """Command to request password reset"""

    user_id: uuid.UUID
