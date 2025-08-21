"""Unit tests for CLI exception handlers.

This module tests the CLI exception handling functionality through the public API
without directly testing private methods.
"""

from unittest.mock import MagicMock, patch

from event_sourcing.cli.handlers.exception import (
    ERROR_MESSAGES,
    EXIT_CODES,
    cli_error_handler,
)
from event_sourcing.exceptions import (
    BusinessRuleViolationError,
    EventSourcingError,
    ResourceConflictError,
    ResourceNotFoundError,
    UserBusinessRuleViolationError,
    UsernameAlreadyExistsError,
    UsernameTooShortError,
    UserNotFoundError,
    ValidationError,
)


class TestCliExceptionHandler:
    """Test the CLI exception handler functionality through public API."""

    def test_exit_codes_mapping(self) -> None:
        """Test that exit codes are correctly mapped for parent exception types."""
        assert EXIT_CODES[ValidationError] == 1
        assert EXIT_CODES[BusinessRuleViolationError] == 1
        assert EXIT_CODES[ResourceNotFoundError] == 2
        assert EXIT_CODES[ResourceConflictError] == 3
        assert EXIT_CODES[EventSourcingError] == 1
        assert EXIT_CODES[Exception] == 1

    def test_error_messages_mapping(self) -> None:
        """Test that error messages are correctly mapped for parent exception types."""
        assert ERROR_MESSAGES[ValidationError] == "Validation error occurred"
        assert (
            ERROR_MESSAGES[BusinessRuleViolationError]
            == "Business rule violation occurred"
        )
        assert ERROR_MESSAGES[ResourceNotFoundError] == "Resource not found"
        assert (
            ERROR_MESSAGES[ResourceConflictError]
            == "Resource conflict occurred"
        )
        assert (
            ERROR_MESSAGES[EventSourcingError]
            == "Event sourcing error occurred"
        )
        assert ERROR_MESSAGES[Exception] == "An unexpected error occurred"

    def test_exit_codes_work_through_public_api(self) -> None:
        """Test that exit codes work correctly through the public API."""

        @cli_error_handler
        def test_validation_error() -> None:
            raise ValidationError("test")

        @cli_error_handler
        def test_resource_not_found() -> None:
            raise ResourceNotFoundError("test")

        @cli_error_handler
        def test_resource_conflict() -> None:
            raise ResourceConflictError("test")

        @cli_error_handler
        def test_unknown_error() -> None:
            class UnknownError(Exception):
                pass

            raise UnknownError("test")

        # Test that validation errors exit with code 1
        with patch("sys.exit") as mock_exit:
            test_validation_error()
            mock_exit.assert_called_with(1)

        # Test that resource not found errors exit with code 2
        with patch("sys.exit") as mock_exit:
            test_resource_not_found()
            mock_exit.assert_called_with(2)

        # Test that resource conflict errors exit with code 3
        with patch("sys.exit") as mock_exit:
            test_resource_conflict()
            mock_exit.assert_called_with(3)

        # Test that unknown errors default to code 1
        with patch("sys.exit") as mock_exit:
            test_unknown_error()
            mock_exit.assert_called_with(1)

    def test_inheritance_works_through_public_api(self) -> None:
        """Test that inheritance relationships work correctly through the public API."""

        @cli_error_handler
        def test_child_validation_error() -> None:
            raise UsernameTooShortError("ab", 3)

        @cli_error_handler
        def test_child_business_error() -> None:
            raise UserBusinessRuleViolationError("test")

        @cli_error_handler
        def test_child_not_found_error() -> None:
            raise UserNotFoundError("test")

        @cli_error_handler
        def test_child_conflict_error() -> None:
            raise UsernameAlreadyExistsError("test")

        # Test that child exceptions inherit parent exit codes
        with patch("sys.exit") as mock_exit:
            test_child_validation_error()
            mock_exit.assert_called_with(1)  # From ValidationError

        with patch("sys.exit") as mock_exit:
            test_child_business_error()
            mock_exit.assert_called_with(1)  # From BusinessRuleViolationError

        with patch("sys.exit") as mock_exit:
            test_child_not_found_error()
            mock_exit.assert_called_with(2)  # From ResourceNotFoundError

        with patch("sys.exit") as mock_exit:
            test_child_conflict_error()
            mock_exit.assert_called_with(3)  # From ResourceConflictError

    def test_error_messages_work_through_public_api(self) -> None:
        """Test that error messages work correctly through the public API."""

        @cli_error_handler
        def test_validation_error() -> None:
            raise ValidationError("Field 'email' is invalid")

        @cli_error_handler
        def test_resource_not_found() -> None:
            raise ResourceNotFoundError("User not found")

        @cli_error_handler
        def test_custom_message() -> None:
            class CustomError(ValidationError):
                def __init__(self, message: str):
                    super().__init__(message)
                    self.message = message

            raise CustomError("Custom validation failed")

        # Test that error messages are displayed through the public API
        with (
            patch("sys.exit"),
            patch(
                "event_sourcing.cli.handlers.exception.typer.echo"
            ) as mock_echo,
        ):
            test_validation_error()
            # Should display error message
            mock_echo.assert_called()

        with (
            patch("sys.exit"),
            patch(
                "event_sourcing.cli.handlers.exception.typer.echo"
            ) as mock_echo,
        ):
            test_resource_not_found()
            # Should display error message
            mock_echo.assert_called()

        with (
            patch("sys.exit"),
            patch(
                "event_sourcing.cli.handlers.exception.typer.echo"
            ) as mock_echo,
        ):
            test_custom_message()
            # Should display error message
            mock_echo.assert_called()

    def test_cli_error_handler_sync_function_success(self) -> None:
        """Test that sync functions work normally when no exception occurs."""

        @cli_error_handler
        def test_func() -> str:
            return "success"

        result = test_func()
        assert result == "success"

    def test_cli_error_handler_async_function_success(self) -> None:
        """Test that async functions work normally when no exception occurs."""

        @cli_error_handler
        async def test_async_func() -> str:
            return "success"

        import asyncio

        result = asyncio.run(test_async_func())
        assert result == "success"

    def test_cli_error_handler_sync_function_validation_error(self) -> None:
        """Test that sync functions handle validation errors correctly."""

        @cli_error_handler
        def test_func() -> None:
            raise ValidationError("test error")

        with patch("sys.exit") as mock_exit:
            test_func()
            mock_exit.assert_called_with(1)

    def test_cli_error_handler_async_function_validation_error(self) -> None:
        """Test that async functions handle validation errors correctly."""

        @cli_error_handler
        async def test_async_func() -> None:
            raise ValidationError("test error")

        import asyncio

        with patch("sys.exit") as mock_exit:
            asyncio.run(test_async_func())
            mock_exit.assert_called_with(1)

    def test_cli_error_handler_sync_function_resource_not_found_error(
        self,
    ) -> None:
        """Test that sync functions handle resource not found errors correctly."""

        @cli_error_handler
        def test_func() -> None:
            raise ResourceNotFoundError("test error")

        with patch("sys.exit") as mock_exit:
            test_func()
            mock_exit.assert_called_with(2)

    def test_cli_error_handler_sync_function_resource_conflict_error(
        self,
    ) -> None:
        """Test that sync functions handle resource conflict errors correctly."""

        @cli_error_handler
        def test_func() -> None:
            raise ResourceConflictError("test error")

        with patch("sys.exit") as mock_exit:
            test_func()
            mock_exit.assert_called_with(3)

    def test_cli_error_handler_sync_function_business_rule_violation_error(
        self,
    ) -> None:
        """Test that sync functions handle business rule violation errors correctly."""

        @cli_error_handler
        def test_func() -> None:
            raise BusinessRuleViolationError("test error")

        with patch("sys.exit") as mock_exit:
            test_func()
            mock_exit.assert_called_with(1)

    def test_cli_error_handler_sync_function_generic_exception(self) -> None:
        """Test that sync functions handle generic exceptions correctly."""

        @cli_error_handler
        def test_func() -> None:
            raise RuntimeError("test error")

        with patch("sys.exit") as mock_exit:
            test_func()
            mock_exit.assert_called_with(1)

    def test_cli_error_handler_preserves_metadata(self) -> None:
        """Test that the decorator preserves function metadata."""

        @cli_error_handler
        def test_func() -> None:
            """Test function docstring."""

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring."

    def test_cli_error_handler_preserves_async_metadata(self) -> None:
        """Test that the decorator preserves async function metadata."""

        @cli_error_handler
        async def test_async_func() -> None:
            """Test async function docstring."""

        assert test_async_func.__name__ == "test_async_func"
        assert test_async_func.__doc__ == "Test async function docstring."

    @patch("sys.exit")
    @patch("event_sourcing.cli.handlers.exception.logger.error")
    @patch("event_sourcing.cli.handlers.exception.typer.echo")
    def test_full_error_handling_flow(
        self,
        mock_echo: MagicMock,
        mock_logger: MagicMock,
        mock_exit: MagicMock,
    ) -> None:
        """Test the complete error handling flow through public API."""

        @cli_error_handler
        def test_func() -> None:
            raise UsernameTooShortError("ab", 3)

        test_func()

        # Verify logging
        mock_logger.assert_called_once()
        log_call = mock_logger.call_args
        assert "CLI command failed" in log_call[0][0]
        assert log_call[1]["exc_info"] is True

        # Verify error display
        mock_echo.assert_called()
        echo_calls = [call.args[0] for call in mock_echo.call_args_list]
        assert any(
            "❌ Validation error occurred" in call for call in echo_calls
        )

        # Verify exit
        mock_exit.assert_called_once_with(1)

    @patch("sys.exit")
    @patch("event_sourcing.cli.handlers.exception.logger.error")
    @patch("event_sourcing.cli.handlers.exception.typer.echo")
    def test_child_exception_inherits_parent_handling(
        self,
        mock_echo: MagicMock,
        mock_logger: MagicMock,
        mock_exit: MagicMock,
    ) -> None:
        """Test that child exceptions inherit parent exception handling through public API."""

        @cli_error_handler
        def test_func() -> None:
            raise UserNotFoundError("User not found")

        test_func()

        # Verify exit code 2 (from ResourceNotFoundError parent)
        mock_exit.assert_called_once_with(2)

        # Verify error message from parent
        echo_calls = [call.args[0] for call in mock_echo.call_args_list]
        assert any("❌ Resource not found" in call for call in echo_calls)

    def test_handle_cli_errors_alias(self) -> None:
        """Test that handle_cli_errors is an alias for cli_error_handler."""
        from event_sourcing.cli.handlers.exception import handle_cli_errors

        @handle_cli_errors
        def test_func() -> str:
            return "success"

        result = test_func()
        assert result == "success"

    def test_both_decorators_work_identically(self) -> None:
        """Test that both decorators work identically."""
        from event_sourcing.cli.handlers.exception import handle_cli_errors

        @cli_error_handler
        def func1() -> None:
            raise ValidationError("test")

        @handle_cli_errors
        def func2() -> None:
            raise ValidationError("test")

        with patch(
            "event_sourcing.cli.handlers.exception._handle_cli_exception"
        ) as mock_handle:
            func1()
            func2()
            assert mock_handle.call_count == 2

    def test_verbose_mode_through_public_api(self) -> None:
        """Test verbose mode functionality through the public API."""

        @cli_error_handler
        def test_func() -> None:
            raise ValidationError("test error", details={"field": "email"})

        # Mock verbose mode to be enabled
        with (
            patch(
                "event_sourcing.cli.handlers.exception._is_verbose_mode",
                return_value=True,
            ),
            patch("sys.exit"),
            patch(
                "event_sourcing.cli.handlers.exception.typer.echo"
            ) as mock_echo,
        ):
            test_func()

            # Should display verbose information
            mock_echo.assert_called()
            # Check that multiple echo calls were made (basic + verbose info)
            assert mock_echo.call_count > 1

    def test_unexpected_exception_traceback_through_public_api(self) -> None:
        """Test that unexpected exceptions show traceback through the public API."""

        @cli_error_handler
        def test_func() -> None:
            raise RuntimeError("unexpected error")

        # Mock verbose mode to be enabled and mark as unexpected exception
        with (
            patch(
                "event_sourcing.cli.handlers.exception._is_verbose_mode",
                return_value=True,
            ),
            patch(
                "event_sourcing.cli.handlers.exception._is_expected_exception",
                return_value=False,
            ),
            patch("sys.exit"),
            patch(
                "event_sourcing.cli.handlers.exception.typer.echo"
            ) as mock_echo,
        ):
            test_func()

            # Should show traceback for unexpected errors
            mock_echo.assert_called()
            # Check that traceback message is displayed
            echo_calls = [call.args[0] for call in mock_echo.call_args_list]
            assert any("Traceback:" in call for call in echo_calls)

    def test_completely_unknown_exception_through_public_api(self) -> None:
        """Test handling of completely unknown exceptions through the public API."""

        class CompletelyUnknownError(Exception):
            def __str__(self) -> str:
                return ""  # Empty string to trigger the else clause

        @cli_error_handler
        def test_func() -> None:
            raise CompletelyUnknownError()

        # Test that unknown exceptions are handled gracefully
        with patch("sys.exit") as mock_exit:
            test_func()
            # Should exit with default code 1
            mock_exit.assert_called_with(1)
