"""Validation-related domain exceptions."""

from typing import Optional

from .domain import DomainError


class ValidationError(DomainError):
    """Exception raised when validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, details)
        self.field = field


class UserValidationError(ValidationError):
    """Exception raised when user validation fails."""


class UsernameTooShortError(UserValidationError):
    """Exception raised when username is too short."""

    def __init__(self, username: str, min_length: int = 3) -> None:
        super().__init__(
            f"Username must be at least {min_length} characters long",
            "username",
            {"username": username, "min_length": min_length},
        )


class PasswordRequiredError(UserValidationError):
    """Exception raised when password is not provided."""

    def __init__(self) -> None:
        super().__init__("Password is required", "password")


class InvalidEmailFormatError(UserValidationError):
    """Exception raised when email format is invalid."""

    def __init__(self, email: str) -> None:
        super().__init__(
            f"Invalid email format: {email}", "email", {"email": email}
        )


class NoFieldsToUpdateError(UserValidationError):
    """Exception raised when no fields are provided for update."""

    def __init__(self) -> None:
        super().__init__("No fields provided for update", "update_fields")


class NewPasswordRequiredError(UserValidationError):
    """Exception raised when new password is not provided."""

    def __init__(self) -> None:
        super().__init__("New password is required", "new_password")


class PasswordMustBeDifferentError(UserValidationError):
    """Exception raised when new password is same as current password."""

    def __init__(self) -> None:
        super().__init__(
            "New password must be different from current password", "password"
        )
