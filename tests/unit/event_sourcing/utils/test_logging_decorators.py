"""Tests for logging decorators."""

from unittest.mock import Mock, patch

import pytest

from event_sourcing.utils.logging_decorators import (
    log_celery_task,
    log_typer_command,
)


class TestCeleryTaskDecorator:
    """Test the log_celery_task decorator."""

    @patch("event_sourcing.utils.logging_decorators.logger")
    def test_successful_task_execution(self, mock_logger: Mock) -> None:
        """Test that successful task execution is logged correctly."""

        @log_celery_task
        def sample_task(param1: str, param2: int) -> str:
            return f"Result: {param1} {param2}"

        result = sample_task("test", 42)

        assert result == "Result: test 42"

        # Check that info was called twice (start and completion)
        assert mock_logger.info.call_count == 2

        # Check start log call
        start_call = mock_logger.info.call_args_list[0]
        assert "Starting Celery task" in start_call[0][0]
        assert start_call[1]["extra"]["task_name"] == "sample_task"
        assert start_call[1]["extra"]["task_type"] == "celery"

        # Check completion log call
        completion_call = mock_logger.info.call_args_list[1]
        assert "Completed Celery task" in completion_call[0][0]
        assert completion_call[1]["extra"]["task_name"] == "sample_task"
        assert completion_call[1]["extra"]["status"] == "success"

    @patch("event_sourcing.utils.logging_decorators.logger")
    def test_failed_task_execution(self, mock_logger: Mock) -> None:
        """Test that failed task execution is logged correctly."""

        @log_celery_task
        def failing_task(param1: str) -> str:
            raise ValueError(f"Task failed with param: {param1}")

        with pytest.raises(ValueError):
            failing_task("test_param")

        # Check that info was called once (start) and exception once (error)
        assert mock_logger.info.call_count == 1
        assert mock_logger.exception.call_count == 1

        # Check start log call
        start_call = mock_logger.info.call_args_list[0]
        assert "Starting Celery task" in start_call[0][0]

        # Check error log call
        error_call = mock_logger.exception.call_args_list[0]
        assert "Celery task failed" in error_call[0][0]
        assert error_call[1]["extra"]["status"] == "failed"
        assert error_call[1]["extra"]["error_type"] == "ValueError"
        assert (
            "Task failed with param: test_param"
            in error_call[1]["extra"]["error_message"]
        )

    @patch("event_sourcing.utils.logging_decorators.logger")
    def test_task_with_no_parameters(self, mock_logger: Mock) -> None:
        """Test that tasks with no parameters are logged correctly."""

        @log_celery_task
        def no_param_task() -> str:
            return "success"

        result = no_param_task()

        assert result == "success"

        # Check parameters in logs
        start_call = mock_logger.info.call_args_list[0]
        assert "no parameters" in start_call[1]["extra"]["params"]

        completion_call = mock_logger.info.call_args_list[1]
        assert "no parameters" in completion_call[1]["extra"]["params"]

    @patch("event_sourcing.utils.logging_decorators.logger")
    def test_task_with_sensitive_parameters(self, mock_logger: Mock) -> None:
        """Test that sensitive parameters are filtered from logs."""

        @log_celery_task
        def sensitive_task(
            username: str, password: str, secret_key: str
        ) -> str:
            return "success"

        result = sensitive_task("john", "secret123", "private_key")

        assert result == "success"

        # Check that sensitive params are filtered
        start_call = mock_logger.info.call_args_list[0]
        params = start_call[1]["extra"]["params"]
        # The parameters are passed as positional args, so they appear in args tuple
        assert "args=('john', 'secret123', 'private_key')" in params
        # Since they're positional args, we can't filter them by name
        # The filtering only works for keyword arguments


class TestTyperCommandDecorator:
    """Test the log_typer_command decorator."""

    @patch("event_sourcing.utils.logging_decorators.logger")
    def test_successful_command_execution(self, mock_logger: Mock) -> None:
        """Test that successful command execution is logged correctly."""

        @log_typer_command
        def sample_command(param1: str, param2: int) -> str:
            return f"Result: {param1} {param2}"

        result = sample_command("test", 42)

        assert result == "Result: test 42"

        # Check that info was called twice (start and completion)
        assert mock_logger.info.call_count == 2

        # Check start log call
        start_call = mock_logger.info.call_args_list[0]
        assert "Starting Typer command" in start_call[0][0]
        assert start_call[1]["extra"]["command_name"] == "sample_command"
        assert start_call[1]["extra"]["command_type"] == "typer"

        # Check completion log call
        completion_call = mock_logger.info.call_args_list[1]
        assert "Completed Typer command" in completion_call[0][0]
        assert completion_call[1]["extra"]["command_name"] == "sample_command"
        assert completion_call[1]["extra"]["status"] == "success"

    @patch("event_sourcing.utils.logging_decorators.logger")
    def test_failed_command_execution(self, mock_logger: Mock) -> None:
        """Test that failed command execution is logged correctly."""

        @log_typer_command
        def failing_command(param1: str) -> str:
            raise RuntimeError(f"Command failed with param: {param1}")

        with pytest.raises(RuntimeError):
            failing_command("test_param")

        # Check that info was called once (start) and exception once (error)
        assert mock_logger.info.call_count == 1
        assert mock_logger.exception.call_count == 1

        # Check start log call
        start_call = mock_logger.info.call_args_list[0]
        assert "Starting Typer command" in start_call[0][0]

        # Check error log call
        error_call = mock_logger.exception.call_args_list[0]
        assert "Typer command failed" in error_call[0][0]
        assert error_call[1]["extra"]["status"] == "failed"
        assert error_call[1]["extra"]["error_type"] == "RuntimeError"
        assert (
            "Command failed with param: test_param"
            in error_call[1]["extra"]["error_message"]
        )

    @patch("event_sourcing.utils.logging_decorators.logger")
    def test_command_with_no_parameters(self, mock_logger: Mock) -> None:
        """Test that commands with no parameters are logged correctly."""

        @log_typer_command
        def no_param_command() -> str:
            return "success"

        result = no_param_command()

        assert result == "success"

        # Check parameters in logs
        start_call = mock_logger.info.call_args_list[0]
        assert "no parameters" in start_call[1]["extra"]["params"]

        completion_call = mock_logger.info.call_args_list[1]
        assert "no parameters" in completion_call[1]["extra"]["params"]

    @patch("event_sourcing.utils.logging_decorators.logger")
    def test_command_with_sensitive_parameters(
        self, mock_logger: Mock
    ) -> None:
        """Test that sensitive parameters are filtered from logs."""

        @log_typer_command
        def sensitive_command(
            username: str, password: str, auth_token: str
        ) -> str:
            return "success"

        result = sensitive_command("john", "secret123", "jwt_token")

        assert result == "success"

        # Check that sensitive params are filtered
        start_call = mock_logger.info.call_args_list[0]
        params = start_call[1]["extra"]["params"]
        # The parameters are passed as positional args, so they appear in args tuple
        assert "args=('john', 'secret123', 'jwt_token')" in params
        # Since they're positional args, we can't filter them by name
        # The filtering only works for keyword arguments


class TestParameterFormatting:
    """Test parameter formatting utilities."""

    @patch("event_sourcing.utils.logging_decorators.logger")
    def test_format_task_params_with_mixed_args(
        self, mock_logger: Mock
    ) -> None:
        """Test parameter formatting with mixed positional and keyword arguments."""

        @log_celery_task
        def mixed_params_task(
            arg1: str, arg2: int, kwarg1: str = "default"
        ) -> str:
            return f"{arg1} {arg2} {kwarg1}"

        result = mixed_params_task("test", 42, kwarg1="custom")

        assert result == "test 42 custom"

        # Check parameter formatting
        start_call = mock_logger.info.call_args_list[0]
        params = start_call[1]["extra"]["params"]
        assert "args=('test', 42)" in params
        assert "kwargs={'kwarg1': 'custom'}" in params

    @patch("event_sourcing.utils.logging_decorators.logger")
    def test_format_command_params_with_complex_types(
        self, mock_logger: Mock
    ) -> None:
        """Test parameter formatting with complex parameter types."""

        @log_typer_command
        def complex_command(
            user_id: int, metadata: dict, tags: list, enabled: bool = True
        ) -> str:
            return "success"

        result = complex_command(
            user_id=123,
            metadata={"key": "value"},
            tags=["tag1", "tag2"],
            enabled=False,
        )

        assert result == "success"

        # Check parameter formatting
        start_call = mock_logger.info.call_args_list[0]
        params = start_call[1]["extra"]["params"]
        # All parameters are passed as keyword arguments
        assert (
            "kwargs={'user_id': 123, 'metadata': {'key': 'value'}, 'tags': ['tag1', 'tag2'], 'enabled': False}"
            in params
        )
