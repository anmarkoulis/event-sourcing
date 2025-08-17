"""CLI handlers package for command-line interface utilities.

This package provides error handling and other utilities for CLI commands.
"""

from .exception import cli_error_handler

__all__ = ["cli_error_handler"]
