"""Domain exceptions package for business logic errors.

This package contains all domain-specific exceptions organized by type:
- domain: Base DomainError
- validation: ValidationError and its children
- business: BusinessRuleViolationError and its children
- resource: ResourceNotFoundError, ResourceConflictError and their children

All exceptions are imported here to maintain backward compatibility.
"""

# Base domain exception
# Business rule violation exceptions
from .business import (
    BusinessRuleViolationError,
    CannotChangePasswordForDeletedUserError,
    CannotUpdateDeletedUserError,
    UserAlreadyDeletedError,
    UserBusinessRuleViolationError,
)
from .domain import DomainError

# Resource exceptions
from .resource import (
    EmailAlreadyExistsError,
    ResourceConflictError,
    ResourceNotFoundError,
    UserAlreadyExistsError,
    UserConflictError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)

# Validation exceptions
from .validation import (
    InvalidEmailFormatError,
    NewPasswordRequiredError,
    NoFieldsToUpdateError,
    PasswordMustBeDifferentError,
    PasswordRequiredError,
    UsernameTooShortError,
    UserValidationError,
    ValidationError,
)

__all__ = [
    # Base
    "DomainError",
    # Validation
    "ValidationError",
    "UserValidationError",
    "UsernameTooShortError",
    "PasswordRequiredError",
    "InvalidEmailFormatError",
    "NoFieldsToUpdateError",
    "NewPasswordRequiredError",
    "PasswordMustBeDifferentError",
    # Business
    "BusinessRuleViolationError",
    "UserBusinessRuleViolationError",
    "CannotUpdateDeletedUserError",
    "CannotChangePasswordForDeletedUserError",
    "UserAlreadyDeletedError",
    # Resource
    "ResourceNotFoundError",
    "ResourceConflictError",
    "UserNotFoundError",
    "UserConflictError",
    "UsernameAlreadyExistsError",
    "EmailAlreadyExistsError",
    "UserAlreadyExistsError",
]
