"""Domain exceptions package for business logic errors.

This package contains all domain-specific exceptions organized by type:
- domain: Base DomainException
- validation: ValidationError and its children
- business: BusinessRuleViolation and its children
- resource: ResourceNotFound, ResourceConflict and their children

All exceptions are imported here to maintain backward compatibility.
"""

# Base domain exception
# Business rule violation exceptions
from .business import (
    BusinessRuleViolation,
    CannotChangePasswordForDeletedUser,
    CannotUpdateDeletedUser,
    UserAlreadyDeleted,
    UserBusinessRuleViolation,
)
from .domain import DomainException

# Resource exceptions
from .resource import (
    EmailAlreadyExists,
    ResourceConflict,
    ResourceNotFound,
    UserAlreadyExists,
    UserConflict,
    UsernameAlreadyExists,
    UserNotFound,
)

# Validation exceptions
from .validation import (
    InvalidEmailFormat,
    NewPasswordRequired,
    NoFieldsToUpdate,
    PasswordMustBeDifferent,
    PasswordRequired,
    UsernameTooShort,
    UserValidationError,
    ValidationError,
)

__all__ = [
    # Base
    "DomainException",
    # Validation
    "ValidationError",
    "UserValidationError",
    "UsernameTooShort",
    "PasswordRequired",
    "InvalidEmailFormat",
    "NoFieldsToUpdate",
    "NewPasswordRequired",
    "PasswordMustBeDifferent",
    # Business
    "BusinessRuleViolation",
    "UserBusinessRuleViolation",
    "CannotUpdateDeletedUser",
    "CannotChangePasswordForDeletedUser",
    "UserAlreadyDeleted",
    # Resource
    "ResourceNotFound",
    "ResourceConflict",
    "UserNotFound",
    "UserConflict",
    "UsernameAlreadyExists",
    "EmailAlreadyExists",
    "UserAlreadyExists",
]
