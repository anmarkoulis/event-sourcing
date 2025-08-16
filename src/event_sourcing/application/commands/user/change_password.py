import uuid

from pydantic import BaseModel


class ChangePasswordCommand(BaseModel):
    """Command to change user's password"""

    user_id: uuid.UUID
    old_password: (
        str  # Plain text old password - will be hashed in command handler
    )
    new_password: (
        str  # Plain text new password - will be hashed in command handler
    )
