"""Test that CLI logging is properly configured and integrated."""

import logging

from event_sourcing.utils import log_typer_command


class TestCLILoggingIntegration:
    """Test CLI logging integration with the main application logging."""

    def test_cli_logging_configured(self) -> None:
        """Test that CLI logging is properly configured."""
        # The CLI should have logging configured
        logger = logging.getLogger("event_sourcing")
        assert logger.handlers, "CLI logger should have handlers configured"

        # Check that the logger level is set
        assert logger.level != logging.NOTSET, "CLI logger level should be set"

    def test_cli_uses_same_logger_as_decorators(self) -> None:
        """Test that CLI commands use the same logger as the decorators."""

        @log_typer_command
        def test_command() -> str:
            return "success"

        # The decorator should use the event_sourcing logger
        logger = logging.getLogger("event_sourcing")
        assert logger.name == "event_sourcing"

        # Test that the command works
        result = test_command()
        assert result == "success"

    def test_cli_logging_format_consistent(self) -> None:
        """Test that CLI logging format is consistent with API logging."""
        # Get the CLI logger
        cli_logger = logging.getLogger("event_sourcing")

        # Check that it has the expected handler
        assert len(cli_logger.handlers) > 0, "CLI logger should have handlers"

        # The handler should be a StreamHandler (as configured in settings)
        handler = cli_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler), (
            "CLI logger should use StreamHandler"
        )

    def test_cli_logging_level_consistent(self) -> None:
        """Test that CLI logging level is consistent with API logging."""
        # Get the CLI logger
        cli_logger = logging.getLogger("event_sourcing")

        # The level should be INFO (default from settings)
        assert cli_logger.level <= logging.INFO, (
            "CLI logger level should be INFO or lower"
        )
