"""Data Transfer Objects (DTOs) for the event sourcing system."""

from .auth import LoginRequest, LoginResponse, TokenData
from .base import ModelConfigBaseModel
from .events import EventDTO
from .events.factory import EventFactory
from .snapshot import SnapshotDTO, UserSnapshotDTO
from .user import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    GetUserHistoryResponse,
    GetUserResponse,
    ListUsersResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    UserDTO,
    UserReadModelData,
)

__all__ = [
    # Base DTOs
    "ModelConfigBaseModel",
    # Auth DTOs
    "LoginRequest",
    "LoginResponse",
    "TokenData",
    # Event DTOs
    "EventDTO",
    "EventFactory",
    # Snapshot DTOs
    "SnapshotDTO",
    "UserSnapshotDTO",
    # User DTOs
    "UserDTO",
    "CreateUserRequest",
    "CreateUserResponse",
    "UpdateUserRequest",
    "UpdateUserResponse",
    "ChangePasswordRequest",
    "ChangePasswordResponse",
    "DeleteUserResponse",
    "GetUserResponse",
    "GetUserHistoryResponse",
    "ListUsersResponse",
    "UserReadModelData",
]
