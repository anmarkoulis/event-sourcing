"""Authentication-related exceptions for security and access control errors."""

from typing import Any, Dict, Optional

from .base import EventSourcingError


class AuthenticationError(EventSourcingError):
    """Base exception for all authentication-related errors."""

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)


class IncorrectPasswordError(AuthenticationError):
    """Exception raised when the provided password is incorrect."""

    def __init__(self, context: str = "authentication") -> None:
        super().__init__(
            f"Password is incorrect for {context}",
            {"context": context},
        )
