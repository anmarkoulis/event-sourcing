"""Base event sourcing exception for all domain-related errors."""

from typing import Any, Dict, Optional


class EventSourcingError(Exception):
    """Base exception for all event sourcing related errors."""

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
