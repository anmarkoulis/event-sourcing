"""Projection-related exceptions for event processing errors."""

from typing import Any, Dict, Optional

from .base import EventSourcingError


class ProjectionError(EventSourcingError):
    """Base exception for all projection-related errors."""

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)


class ProjectionProcessingError(ProjectionError):
    """Exception raised when projection processing fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        projection_name: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> None:
        super().__init__(message, details)
        self.projection_name = projection_name
        self.event_type = event_type


class EmailProjectionError(ProjectionProcessingError):
    """Exception raised when email projection processing fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        email_type: Optional[str] = None,
        recipient: Optional[str] = None,
    ) -> None:
        super().__init__(message, details)
        self.email_type = email_type
        self.recipient = recipient


class ProjectionConfigurationError(ProjectionError):
    """Exception raised when projection configuration is invalid."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.config_key = config_key


class ProjectionDependencyError(ProjectionError):
    """Exception raised when projection dependencies are missing or invalid."""

    def __init__(
        self,
        message: str,
        dependency: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.dependency = dependency
