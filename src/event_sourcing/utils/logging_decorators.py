"""Logging decorators for entrypoints and tasks.

This module provides decorators for consistent logging across different entrypoints:
- Celery tasks
- Typer CLI commands

The decorators follow the logging philosophy where info level is only for entrypoints
(start and end), while debug level is used for internal operations.
"""

import functools
import logging
from typing import Any, Callable, TypeVar, cast

# Use the same logger as the API and Celery tasks
logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def log_celery_task(func: F) -> F:
    """Decorator to log Celery task execution with consistent logging.

    Logs at info level when task starts and finishes, and logs exceptions
    at error level. This follows the logging philosophy where info level
    is only for entrypoints.

    :param func: The Celery task function to decorate.
    :return: Decorated function with logging.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        task_name = func.__name__
        params_str = _format_task_params(args, kwargs)

        try:
            logger.info(
                f"Starting Celery task: {task_name}",
                extra={
                    "task_name": task_name,
                    "params": params_str,
                    "task_type": "celery",
                    "worker_id": getattr(func, "_worker_id", "unknown"),
                    "task_id": getattr(func, "_task_id", "unknown"),
                },
            )

            result = func(*args, **kwargs)

            logger.info(
                f"Completed Celery task: {task_name}",
                extra={
                    "task_name": task_name,
                    "params": params_str,
                    "task_type": "celery",
                    "status": "success",
                    "worker_id": getattr(func, "_worker_id", "unknown"),
                    "task_id": getattr(func, "_task_id", "unknown"),
                },
            )

            return result

        except Exception as e:
            logger.exception(
                f"Celery task failed: {task_name}",
                extra={
                    "task_name": task_name,
                    "params": params_str,
                    "task_type": "celery",
                    "status": "failed",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "worker_id": getattr(func, "_worker_id", "unknown"),
                    "task_id": getattr(func, "_task_id", "unknown"),
                },
            )
            raise

    return cast(F, wrapper)


def log_typer_command(func: F) -> F:
    """Decorator to log Typer command execution with consistent logging.

    Logs at info level when command starts and finishes, and logs exceptions
    at error level. This follows the logging philosophy where info level
    is only for entrypoints.

    :param func: The Typer command function to decorate.
    :return: Decorated function with logging.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        command_name = func.__name__
        params_str = _format_command_params(args, kwargs)

        try:
            logger.info(
                f"Starting Typer command: {command_name}",
                extra={
                    "command_name": command_name,
                    "params": params_str,
                    "command_type": "typer",
                },
            )

            result = func(*args, **kwargs)

            logger.info(
                f"Completed Typer command: {command_name}",
                extra={
                    "command_name": command_name,
                    "params": params_str,
                    "command_type": "typer",
                    "status": "success",
                },
            )

            return result

        except Exception as e:
            logger.exception(
                f"Typer command failed: {command_name}",
                extra={
                    "command_name": command_name,
                    "params": params_str,
                    "command_type": "typer",
                    "status": "failed",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            raise

    return cast(F, wrapper)


def _format_task_params(args: tuple, kwargs: dict) -> str:
    """Format task parameters for logging.

    :param args: Positional arguments.
    :param kwargs: Keyword arguments.
    :return: Formatted string representation of parameters.
    """
    if not args and not kwargs:
        return "no parameters"

    parts = []

    if args:
        parts.append(f"args={args}")

    if kwargs:
        # Filter out sensitive parameters
        safe_kwargs = {
            k: v for k, v in kwargs.items() if not _is_sensitive_param(k)
        }
        if safe_kwargs:
            parts.append(f"kwargs={safe_kwargs}")

    return ", ".join(parts) if parts else "no parameters"


def _format_command_params(args: tuple, kwargs: dict) -> str:
    """Format command parameters for logging.

    :param args: Positional arguments.
    :param kwargs: Keyword arguments.
    :return: Formatted string representation of parameters.
    """
    if not args and not kwargs:
        return "no parameters"

    parts = []

    if args:
        parts.append(f"args={args}")

    if kwargs:
        # Filter out sensitive parameters
        safe_kwargs = {
            k: v for k, v in kwargs.items() if not _is_sensitive_param(k)
        }
        if safe_kwargs:
            parts.append(f"kwargs={safe_kwargs}")

    return ", ".join(parts) if parts else "no parameters"


def _is_sensitive_param(param_name: str) -> bool:
    """Check if a parameter name indicates sensitive data.

    :param param_name: Name of the parameter to check.
    :return: True if the parameter contains sensitive data.
    """
    sensitive_patterns = [
        "password",
        "secret",
        "token",
        "key",
        "auth",
        "credential",
        "private",
        "sensitive",
        "hash",
        "salt",
        "nonce",
    ]

    param_lower = param_name.lower()
    return any(pattern in param_lower for pattern in sensitive_patterns)
