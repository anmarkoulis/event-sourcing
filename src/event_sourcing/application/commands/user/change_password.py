import uuid

from pydantic import BaseModel


class ChangePasswordCommand(BaseModel):
    """Command to change user's password"""

    user_id: uuid.UUID
    new_password_hash: str
