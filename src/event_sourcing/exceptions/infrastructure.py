"""Infrastructure-related exceptions for system and configuration errors."""

from typing import Any, Dict, Optional

from .base import EventSourcingError


class InfrastructureError(EventSourcingError):
    """Base exception for all infrastructure-related errors."""

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)


class UnsupportedAggregateTypeError(InfrastructureError):
    """Exception raised when an unsupported aggregate type is requested."""

    def __init__(self, aggregate_type: str) -> None:
        super().__init__(
            f"Unsupported aggregate type: {aggregate_type}",
            {"aggregate_type": aggregate_type},
        )


class UnknownProviderError(InfrastructureError):
    """Exception raised when an unknown provider is requested."""

    def __init__(
        self, provider_name: str, provider_type: str = "provider"
    ) -> None:
        super().__init__(
            f"Unknown {provider_type}: {provider_name}",
            {"provider_name": provider_name, "provider_type": provider_type},
        )


class MissingRequiredFieldError(InfrastructureError):
    """Exception raised when a required field is missing."""

    def __init__(self, field_name: str, context: str = "data") -> None:
        super().__init__(
            f"{field_name} is required for {context}",
            {"field_name": field_name, "context": context},
        )


class ConfigurationError(InfrastructureError):
    """Exception raised when there's a configuration error."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.config_key = config_key


class SerializationError(InfrastructureError):
    """Exception raised when serialization/deserialization fails."""

    def __init__(
        self,
        message: str,
        data_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.data_type = data_type


class DatabaseError(InfrastructureError):
    """Exception raised when database operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.operation = operation
