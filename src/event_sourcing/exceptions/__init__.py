"""Event sourcing exceptions package for business logic errors.

This package contains all event sourcing specific exceptions organized by type:
- base: Base EventSourcingError
- validation: ValidationError and its children
- business: BusinessRuleViolationError and its children
- resource: ResourceNotFoundError, ResourceConflictError and their children
- infrastructure: InfrastructureError and its children
- authentication: AuthenticationError and its children

All exceptions are imported here to maintain backward compatibility.
"""

# Base event sourcing exception
# Authentication exceptions
from .authentication import (
    AuthenticationError,
    AuthenticationFailedError,
    IncorrectPasswordError,
    InsufficientPermissionsError,
    InvalidPasswordError,
    PasswordMismatchError,
)
from .base import EventSourcingError

# Business rule violation exceptions
from .business import (
    BusinessRuleViolationError,
    CannotChangePasswordForDeletedUserError,
    CannotUpdateDeletedUserError,
    UserAlreadyDeletedError,
    UserBusinessRuleViolationError,
)

# Infrastructure exceptions
from .infrastructure import (
    ConfigurationError,
    DatabaseError,
    InfrastructureError,
    MissingRequiredFieldError,
    SerializationError,
    UnknownProviderError,
    UnsupportedAggregateTypeError,
)

# Projection exceptions
from .projection import (
    EmailProjectionError,
    ProjectionConfigurationError,
    ProjectionDependencyError,
    ProjectionError,
    ProjectionProcessingError,
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
    # Infrastructure
    "InfrastructureError",
    "UnsupportedAggregateTypeError",
    "UnknownProviderError",
    "MissingRequiredFieldError",
    "ConfigurationError",
    "SerializationError",
    "DatabaseError",
    # Authentication
    "AuthenticationError",
    "InvalidPasswordError",
    "IncorrectPasswordError",
    "PasswordMismatchError",
    "AuthenticationFailedError",
    "InsufficientPermissionsError",
    # Projection
    "ProjectionError",
    "ProjectionProcessingError",
    "EmailProjectionError",
    "ProjectionConfigurationError",
    "ProjectionDependencyError",
]
