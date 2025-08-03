import uuid

from pydantic import BaseModel


class ChangeUsernameCommand(BaseModel):
    """Command to change user's username"""

    user_id: uuid.UUID
    new_username: str
