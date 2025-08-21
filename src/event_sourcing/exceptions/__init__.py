"""Event sourcing exceptions package for business logic errors.

This package contains all event sourcing specific exceptions organized by type:
- base: Base EventSourcingError
- validation: ValidationError and its children
- business: BusinessRuleViolationError and its children
- resource: ResourceNotFoundError, ResourceConflictError and their children

All exceptions are imported here to maintain backward compatibility.
"""

# Base event sourcing exception
# Business rule violation exceptions
from .base import EventSourcingError
from .business import (
    BusinessRuleViolationError,
    CannotChangePasswordForDeletedUserError,
    CannotUpdateDeletedUserError,
    UserAlreadyDeletedError,
    UserBusinessRuleViolationError,
)

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
    "EventSourcingError",
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
