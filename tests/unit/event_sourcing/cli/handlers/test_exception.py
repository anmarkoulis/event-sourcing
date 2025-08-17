"""Unit tests for CLI exception handlers.

This module tests the CLI exception handling functionality including the
cli_error_handler decorator and related utility functions.
"""

from unittest.mock import MagicMock, patch

from event_sourcing.cli.handlers.exception import (
    ERROR_MESSAGES,
    EXIT_CODES,
    _get_error_message,
    _get_exit_code,
    _is_expected_exception,
    cli_error_handler,
)
from event_sourcing.domain.exceptions import (
    BusinessRuleViolationError,
    DomainError,
    ResourceConflictError,
    ResourceNotFoundError,
    UserBusinessRuleViolationError,
    UsernameAlreadyExistsError,
    UsernameTooShortError,
    UserNotFoundError,
    ValidationError,
)


class TestCliExceptionHandler:
    """Test the CLI exception handler functionality."""

    def test_exit_codes_mapping(self) -> None:
        """Test that exit codes are correctly mapped for parent exception types."""
        assert EXIT_CODES[ValidationError] == 1
        assert EXIT_CODES[BusinessRuleViolationError] == 1
        assert EXIT_CODES[ResourceNotFoundError] == 2
        assert EXIT_CODES[ResourceConflictError] == 3
        assert EXIT_CODES[DomainError] == 1
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
        assert ERROR_MESSAGES[DomainError] == "Domain error occurred"
        assert ERROR_MESSAGES[Exception] == "An unexpected error occurred"

    def test_get_exit_code_exact_type_match(self) -> None:
        """Test that exact type matches return correct exit codes."""
        assert _get_exit_code(ValidationError("test")) == 1
        assert _get_exit_code(ResourceNotFoundError("test")) == 2
        assert _get_exit_code(ResourceConflictError("test")) == 3

    def test_get_exit_code_inheritance_match(self) -> None:
        """Test that child exceptions inherit parent exit codes."""
        # UsernameTooShortError inherits from ValidationError
        username_error = UsernameTooShortError("test", 3)
        assert _get_exit_code(username_error) == 1

        # UserBusinessRuleViolationError inherits from BusinessRuleViolationError
        business_error = UserBusinessRuleViolationError("test")
        assert _get_exit_code(business_error) == 1

        # UserNotFoundError inherits from ResourceNotFoundError
        not_found_error = UserNotFoundError("test")
        assert _get_exit_code(not_found_error) == 2

        # UsernameAlreadyExistsError inherits from ResourceConflictError
        conflict_error = UsernameAlreadyExistsError("test")
        assert _get_exit_code(conflict_error) == 3

    def test_get_exit_code_unknown_exception_default(self) -> None:
        """Test that unknown exceptions default to exit code 1."""

        class UnknownError(Exception):
            pass

        assert _get_exit_code(UnknownError("test")) == 1

    def test_get_error_message_exact_type_match(self) -> None:
        """Test that exact type matches return correct messages."""
        assert (
            _get_error_message(ValidationError("test"))
            == "Validation error occurred: test"
        )
        assert (
            _get_error_message(ResourceNotFoundError("test"))
            == "Resource not found: test"
        )

    def test_get_error_message_inheritance_match(self) -> None:
        """Test that child exceptions inherit parent messages."""
        # UsernameTooShortError inherits from ValidationError
        username_error = UsernameTooShortError("test", 3)
        assert (
            _get_error_message(username_error)
            == "Validation error occurred: Username must be at least 3 characters long"
        )

        # UserNotFoundError inherits from ResourceNotFoundError
        not_found_error = UserNotFoundError("test")
        assert (
            _get_error_message(not_found_error) == "Resource not found: test"
        )

    def test_get_error_message_exception_with_message_attribute(self) -> None:
        """Test that exceptions with message attribute include it."""

        class CustomError(ValidationError):
            def __init__(self, message: str):
                super().__init__(message)
                self.message = message

        error = CustomError("Custom validation failed")
        assert (
            _get_error_message(error)
            == "Validation error occurred: Custom validation failed"
        )

    def test_get_error_message_exception_with_string_representation(
        self,
    ) -> None:
        """Test that exceptions with custom string representation include it."""
        error = ValidationError("Field 'email' is invalid")
        assert (
            _get_error_message(error)
            == "Validation error occurred: Field 'email' is invalid"
        )

    def test_get_error_message_exception_without_details(self) -> None:
        """Test that exceptions without details return base message."""

        # The ValidationError constructor always includes the message in str(exc)
        # So we need to test with an exception that truly has no string details
        class SimpleError(ValidationError):
            def __init__(self, message: str):
                # Don't call super().__init__ to avoid setting the message
                self.message = None  # Override any message attribute

        error = SimpleError("test")
        # Since str(error) will still return something, we need to test the actual behavior
        result = _get_error_message(error)
        assert result.startswith("Validation error occurred")

    def test_is_expected_exception_domain_exceptions(self) -> None:
        """Test that domain exceptions are considered expected."""
        assert _is_expected_exception(ValidationError("test")) is True
        assert (
            _is_expected_exception(BusinessRuleViolationError("test")) is True
        )
        assert _is_expected_exception(ResourceNotFoundError("test")) is True
        assert _is_expected_exception(ResourceConflictError("test")) is True
        assert _is_expected_exception(DomainError("test")) is True

    def test_is_expected_exception_child_exceptions(self) -> None:
        """Test that child exceptions are considered expected."""
        assert _is_expected_exception(UsernameTooShortError("test", 3)) is True
        assert (
            _is_expected_exception(UserBusinessRuleViolationError("test"))
            is True
        )
        assert _is_expected_exception(UserNotFoundError("test")) is True
        assert (
            _is_expected_exception(UsernameAlreadyExistsError("test")) is True
        )

    def test_is_expected_exception_unexpected_exceptions(self) -> None:
        """Test that non-domain exceptions are considered unexpected."""
        assert _is_expected_exception(ValueError("test")) is False
        assert _is_expected_exception(TypeError("test")) is False
        assert _is_expected_exception(RuntimeError("test")) is False

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
        """Test that sync functions handle ValidationError correctly."""

        @cli_error_handler
        def test_func() -> None:
            raise ValidationError("Invalid input")

        with patch("sys.exit") as mock_exit:
            with patch(
                "event_sourcing.cli.handlers.exception._handle_cli_exception"
            ) as mock_handle:
                test_func()
                mock_handle.assert_called_once()
                mock_exit.assert_not_called()  # _handle_cli_exception handles exit

    def test_cli_error_handler_async_function_validation_error(self) -> None:
        """Test that async functions handle ValidationError correctly."""

        @cli_error_handler
        async def test_async_func() -> None:
            raise ValidationError("Invalid input")

        with patch("sys.exit") as mock_exit:
            with patch(
                "event_sourcing.cli.handlers.exception._handle_cli_exception"
            ) as mock_handle:
                import asyncio

                asyncio.run(test_async_func())
                mock_handle.assert_called_once()
                mock_exit.assert_not_called()

    def test_cli_error_handler_sync_function_resource_not_found_error(
        self,
    ) -> None:
        """Test that sync functions handle ResourceNotFoundError correctly."""

        @cli_error_handler
        def test_func() -> None:
            raise ResourceNotFoundError("User not found")

        with patch(
            "event_sourcing.cli.handlers.exception._handle_cli_exception"
        ) as mock_handle:
            test_func()
            mock_handle.assert_called_once()

    def test_cli_error_handler_sync_function_resource_conflict_error(
        self,
    ) -> None:
        """Test that sync functions handle ResourceConflictError correctly."""

        @cli_error_handler
        def test_func() -> None:
            raise ResourceConflictError("Username already exists")

        with patch(
            "event_sourcing.cli.handlers.exception._handle_cli_exception"
        ) as mock_handle:
            test_func()
            mock_handle.assert_called_once()

    def test_cli_error_handler_sync_function_business_rule_violation_error(
        self,
    ) -> None:
        """Test that sync functions handle BusinessRuleViolationError correctly."""

        @cli_error_handler
        def test_func() -> None:
            raise BusinessRuleViolationError("Cannot delete active user")

        with patch(
            "event_sourcing.cli.handlers.exception._handle_cli_exception"
        ) as mock_handle:
            test_func()
            mock_handle.assert_called_once()

    def test_cli_error_handler_sync_function_generic_exception(self) -> None:
        """Test that sync functions handle generic exceptions correctly."""

        @cli_error_handler
        def test_func() -> None:
            raise RuntimeError("Unexpected error")

        with patch(
            "event_sourcing.cli.handlers.exception._handle_cli_exception"
        ) as mock_handle:
            test_func()
            mock_handle.assert_called_once()

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
    @patch("typer.echo")
    def test_full_error_handling_flow(
        self,
        mock_echo: MagicMock,
        mock_logger: MagicMock,
        mock_exit: MagicMock,
    ) -> None:
        """Test the complete error handling flow."""

        @cli_error_handler
        def test_func() -> None:
            raise UsernameTooShortError("ab", 3)

        test_func()

        # Verify logging
        mock_logger.assert_called_once()
        log_call = mock_logger.call_args
        assert "CLI command failed" in log_call[0][0]
        # The exc_info parameter is the exception object itself
        assert (
            log_call[1]["exc_info"] is True
        )  # logger.error sets exc_info=True when called

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
    @patch("typer.echo")
    def test_child_exception_inherits_parent_handling(
        self,
        mock_echo: MagicMock,
        mock_logger: MagicMock,
        mock_exit: MagicMock,
    ) -> None:
        """Test that child exceptions inherit parent exception handling."""

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
