"""CLI exception handlers for mapping domain exceptions to exit codes.

This module provides error handling for CLI commands, mapping domain exceptions
to appropriate exit codes and providing consistent error formatting.
"""

import functools
import logging
import sys
import traceback
from typing import Any, Callable, TypeVar

import typer

from event_sourcing.exceptions import (
    BusinessRuleViolationError,
    EventSourcingError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)

# Type variable for function return type
F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)

# Exit code mapping for different exception types
EXIT_CODES = {
    # Validation errors - 1 (general error)
    ValidationError: 1,
    # Business rule violations - 1 (business logic error)
    BusinessRuleViolationError: 1,
    # Resource not found - 2 (not found)
    ResourceNotFoundError: 2,
    # Resource conflicts - 3 (conflict)
    ResourceConflictError: 3,
    # Event sourcing errors - 1 (general event sourcing error)
    EventSourcingError: 1,
    # Generic exceptions - 1 (unexpected error)
    Exception: 1,
}

# User-friendly error messages
ERROR_MESSAGES = {
    ValidationError: "Validation error occurred",
    BusinessRuleViolationError: "Business rule violation occurred",
    ResourceNotFoundError: "Resource not found",
    ResourceConflictError: "Resource conflict occurred",
    EventSourcingError: "Event sourcing error occurred",
    Exception: "An unexpected error occurred",
}


def cli_error_handler(func: F) -> F:
    """Decorator to handle exceptions in CLI commands.

    This decorator catches domain exceptions and maps them to appropriate
    exit codes, providing consistent error formatting and logging.

    :param func: The function to wrap with error handling.
    :return: Wrapped function with error handling.

    Example:
        @cli_error_handler
        def my_command():
            # Your command logic here
            pass
    """

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper for synchronous functions."""
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            _handle_cli_exception(exc)

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper for asynchronous functions."""
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            _handle_cli_exception(exc)

    # Return the appropriate wrapper based on whether the function is async
    if _is_async_function(func):
        return async_wrapper  # type: ignore
    else:
        return sync_wrapper  # type: ignore


def _is_async_function(func: Callable[..., Any]) -> bool:
    """Check if a function is asynchronous.

    :param func: Function to check.
    :return: True if the function is async, False otherwise.
    """
    import inspect

    return inspect.iscoroutinefunction(func)


def _handle_cli_exception(exc: Exception) -> None:
    """Handle CLI exceptions by mapping to exit codes and formatting output.

    :param exc: The exception that occurred.
    """
    # Determine exit code
    exit_code = _get_exit_code(exc)

    # Get user-friendly message
    message = _get_error_message(exc)

    # Log the error
    logger.error(f"CLI command failed: {exc}", exc_info=True)

    # Format and display error
    _display_error(exc, message)

    # Exit with appropriate code
    sys.exit(exit_code)


def _get_exit_code(exc: Exception) -> int:
    """Get the appropriate exit code for an exception.

    :param exc: The exception that occurred.
    :return: Exit code for the exception.
    """
    # Check for exact type match first
    exc_type = type(exc)
    if exc_type in EXIT_CODES:
        return EXIT_CODES[exc_type]

    # Check for inheritance relationships
    for base_type, exit_code in EXIT_CODES.items():
        if isinstance(exc, base_type):
            return exit_code

    # Default to general error
    return 1


def _get_error_message(exc: Exception) -> str:
    """Get a user-friendly error message for an exception.

    :param exc: The exception that occurred.
    :return: User-friendly error message.
    """
    # Check for exact type match first
    exc_type = type(exc)
    if exc_type in ERROR_MESSAGES:
        base_message = ERROR_MESSAGES[exc_type]
    else:
        # Check for inheritance relationships
        for base_type, message in ERROR_MESSAGES.items():
            if isinstance(exc, base_type):
                base_message = message
                break
        else:
            base_message = ERROR_MESSAGES[Exception]

    # Add specific details if available
    if hasattr(exc, "message") and exc.message:
        return f"{base_message}: {exc.message}"
    elif str(exc) and str(exc) != exc.__class__.__name__:
        return f"{base_message}: {str(exc)}"
    else:
        return base_message


def _display_error(exc: Exception, message: str) -> None:
    """Display the error message in a user-friendly format.

    :param exc: The exception that occurred.
    :param message: User-friendly error message.
    """
    # Use typer for consistent styling
    typer.echo(f"❌ {message}", err=True)

    # Add additional context for debugging if in verbose mode
    if _is_verbose_mode():
        typer.echo(f"Exception type: {exc.__class__.__name__}", err=True)
        if hasattr(exc, "details") and exc.details:
            typer.echo(f"Details: {exc.details}", err=True)

        # Show traceback for unexpected errors
        if not _is_expected_exception(exc):
            typer.echo("Traceback:", err=True)
            traceback.print_exception(
                type(exc), exc, exc.__traceback__, file=sys.stderr
            )


def _is_verbose_mode() -> bool:
    """Check if verbose mode is enabled.

    :return: True if verbose mode is enabled, False otherwise.
    """
    # This could be enhanced to check for --verbose flags or environment variables
    return False


def _is_expected_exception(exc: Exception) -> bool:
    """Check if an exception is expected (domain exception) vs unexpected.

    :param exc: The exception that occurred.
    :return: True if the exception is expected, False otherwise.
    """
    expected_types = {
        ValidationError,
        BusinessRuleViolationError,
        ResourceNotFoundError,
        ResourceConflictError,
        EventSourcingError,
    }

    return any(
        isinstance(exc, expected_type) for expected_type in expected_types
    )


def handle_cli_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Alternative function decorator for handling CLI errors.

    This is an alias for cli_error_handler for backward compatibility.

    :param func: The function to wrap with error handling.
    :return: Wrapped function with error handling.
    """
    return cli_error_handler(func)
