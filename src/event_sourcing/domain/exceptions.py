"""Domain exceptions for business logic errors.

This module defines the exception hierarchy for domain-specific errors
that can occur during business operations. These exceptions are raised
from aggregates and handlers and then mapped to appropriate responses
by the exception handlers (HTTP status codes, exit codes, etc.).
"""

from typing import Any, Dict, Optional


class DomainException(Exception):
    """Base exception for all domain-related errors."""

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(DomainException):
    """Exception raised when validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.field = field


class BusinessRuleViolation(DomainException):
    """Exception raised when business rules are violated."""

    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.rule_name = rule_name


class ResourceNotFound(DomainException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
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
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.conflict_type = conflict_type


# User-specific exceptions
class UserValidationError(ValidationError):
    """Exception raised when user validation fails."""


class UserBusinessRuleViolation(BusinessRuleViolation):
    """Exception raised when user business rules are violated."""


class UserNotFound(ResourceNotFound):
    """Exception raised when a user is not found."""

    def __init__(
        self,
        message: str = "User not found",
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, "User", user_id, details)
        self.user_id = user_id


class UserConflict(ResourceConflict):
    """Exception raised when there's a conflict with an existing user."""

    def __init__(
        self,
        message: str,
        conflict_field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
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


class UsernameTooShort(UserValidationError):
    """Exception raised when username is too short."""

    def __init__(self, username: str, min_length: int = 3) -> None:
        super().__init__(
            f"Username must be at least {min_length} characters long",
            "username",
            {"username": username, "min_length": min_length},
        )


class PasswordRequired(UserValidationError):
    """Exception raised when password is not provided."""

    def __init__(self) -> None:
        super().__init__("Password is required", "password")


class InvalidEmailFormat(UserValidationError):
    """Exception raised when email format is invalid."""

    def __init__(self, email: str) -> None:
        super().__init__(
            f"Invalid email format: {email}", "email", {"email": email}
        )
