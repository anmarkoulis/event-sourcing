"""Resource-related domain exceptions."""

from typing import Optional

from .domain import DomainException


class ResourceNotFound(DomainException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceConflict(DomainException):
    """Exception raised when there's a conflict with an existing resource."""

    def __init__(
        self,
        message: str,
        conflict_type: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, details)
        self.conflict_type = conflict_type


# User-specific resource exceptions
class UserNotFound(ResourceNotFound):
    """Exception raised when a user is not found."""

    def __init__(
        self,
        message: str = "User not found",
        user_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, "User", user_id, details)
        self.user_id = user_id


class UserConflict(ResourceConflict):
    """Exception raised when there's a conflict with an existing user."""

    def __init__(
        self,
        message: str,
        conflict_field: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, "User", details)
        self.conflict_field = conflict_field


class UsernameAlreadyExists(UserConflict):
    """Exception raised when trying to create a user with an existing username."""

    def __init__(self, username: str) -> None:
        super().__init__(
            f"Username '{username}' already exists",
            "username",
            {"username": username},
        )


class EmailAlreadyExists(UserConflict):
    """Exception raised when trying to create a user with an existing email."""

    def __init__(self, email: str) -> None:
        super().__init__(
            f"Email '{email}' already exists", "email", {"email": email}
        )


class UserAlreadyExists(UserConflict):
    """Exception raised when trying to create a user that already exists."""

    def __init__(self, username: str) -> None:
        super().__init__(
            f"User '{username}' already exists",
            "user",
            {"username": username},
        )
