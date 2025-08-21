"""Authentication-related exceptions for security and access control errors."""

from typing import Any, Dict, Optional

from .base import EventSourcingError


class AuthenticationError(EventSourcingError):
    """Base exception for all authentication-related errors."""

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)


class InvalidPasswordError(AuthenticationError):
    """Exception raised when password validation fails."""

    def __init__(self, reason: str = "Password is invalid") -> None:
        super().__init__(reason, {"reason": reason})


class IncorrectPasswordError(AuthenticationError):
    """Exception raised when the provided password is incorrect."""

    def __init__(self, context: str = "authentication") -> None:
        super().__init__(
            f"Password is incorrect for {context}",
            {"context": context},
        )


class PasswordMismatchError(AuthenticationError):
    """Exception raised when passwords don't match during verification."""

    def __init__(self, operation: str = "verification") -> None:
        super().__init__(
            f"Password mismatch during {operation}",
            {"operation": operation},
        )


class AuthenticationFailedError(AuthenticationError):
    """Exception raised when authentication fails."""

    def __init__(
        self,
        reason: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(reason, details)
        self.user_id = user_id
        self.reason = reason


class InsufficientPermissionsError(AuthenticationError):
    """Exception raised when user lacks required permissions."""

    def __init__(
        self,
        required_permission: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            f"Insufficient permissions: {required_permission} required",
            details,
        )
        self.required_permission = required_permission
        self.user_id = user_id
