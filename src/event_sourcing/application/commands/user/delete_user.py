import uuid

from pydantic import BaseModel


class DeleteUserCommand(BaseModel):
    """Command to delete user"""

    user_id: uuid.UUID
