import uuid

from pydantic import BaseModel, EmailStr

from event_sourcing.enums import HashingMethod, Role


class CreateUserCommand(BaseModel):
    """Command to create a new user"""

    user_id: uuid.UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str  # Plain text password - will be hashed in command handler
    hashing_method: HashingMethod = (
        HashingMethod.BCRYPT
    )  # Default hashing method
    role: Role = Role.USER  # Default role is USER
