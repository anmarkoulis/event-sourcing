import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr


class UpdateUserCommand(BaseModel):
    """Command to update user information"""

    user_id: uuid.UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
