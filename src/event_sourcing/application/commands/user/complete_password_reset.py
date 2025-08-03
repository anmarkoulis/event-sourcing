import uuid

from pydantic import BaseModel


class CompletePasswordResetCommand(BaseModel):
    """Command to complete password reset"""

    user_id: uuid.UUID
    new_password_hash: str
    reset_token: str
