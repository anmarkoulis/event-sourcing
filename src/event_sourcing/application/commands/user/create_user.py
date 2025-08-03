import uuid

from pydantic import BaseModel, EmailStr


class CreateUserCommand(BaseModel):
    """Command to create a new user"""

    user_id: uuid.UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password_hash: str
