"""Infrastructure-specific enums."""

from enum import Enum


class HashingMethod(str, Enum):
    """Available hashing methods for passwords."""

    BCRYPT = "bcrypt"
