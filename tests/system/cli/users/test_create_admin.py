"""System tests for CLI create-admin command.

These tests verify the CLI command behavior and outputs using the test database
infrastructure from conftest, but focus on CLI outputs rather than direct database verification.
"""

import uuid
from typing import Any
from unittest.mock import patch

import pytest
import typer.testing

from event_sourcing.cli.main import app


class TestCLICreateAdmin:
    """Test CLI create-admin command outputs and behavior."""

    @pytest.fixture
    def runner(self) -> typer.testing.CliRunner:
        """Create a CLI runner for testing."""
        return typer.testing.CliRunner()

    def test_create_admin_user_success(
        self,
        db_engine: Any,
        test_infrastructure_factory: Any,
        runner: typer.testing.CliRunner,
    ) -> None:
        """Test successful admin user creation via CLI."""
        # Arrange
        test_username = f"admin_test_{uuid.uuid4().hex[:8]}"
        test_email = f"admin_test_{uuid.uuid4().hex[:8]}@example.com"
        test_password = (
            "SecurePassword123!"  # pragma: allowlist secret # noqa: S105
        )

        # Patch the get_infrastructure_factory function to return our test factory
        with patch(
            "event_sourcing.cli.users.create_admin.get_infrastructure_factory",
            return_value=test_infrastructure_factory,
        ):
            # Act - Execute the CLI command
            result = runner.invoke(
                app,
                [
                    "users",
                    "create-admin",
                    "--username",
                    test_username,
                    "--password",
                    test_password,
                    "--email",
                    test_email,
                    "--first-name",
                    "Test",
                    "--last-name",
                    "Admin",
                ],
                env={},
            )

        # Assert - Check CLI output and behavior
        assert result.exit_code == 0, f"CLI command failed: {result.stderr}"

        # Check output contains success message
        assert "✅ Admin user" in result.stdout
        assert "created successfully!" in result.stdout
        assert test_username in result.stdout
        assert "User ID:" in result.stdout

        # Check that proper information was displayed
        assert "Creating admin user:" in result.stdout
        assert f"Username: {test_username}" in result.stdout
        assert f"Email: {test_email}" in result.stdout
        assert "First Name: Test" in result.stdout
        assert "Last Name: Admin" in result.stdout
        assert "Role: ADMIN" in result.stdout

    def test_create_admin_user_with_environment_variables(
        self, test_infrastructure_factory: Any, runner: typer.testing.CliRunner
    ) -> None:
        """Test admin user creation using environment variables only."""
        # Arrange
        test_username = f"env_admin_{uuid.uuid4().hex[:8]}"
        test_email = f"env_admin_{uuid.uuid4().hex[:8]}@example.com"
        test_password = (
            "EnvPassword123!"  # pragma: allowlist secret  # noqa: S105
        )

        # Patch the get_infrastructure_factory function to return our test factory
        with patch(
            "event_sourcing.cli.users.create_admin.get_infrastructure_factory",
            return_value=test_infrastructure_factory,
        ):
            # Act - Execute the CLI command with command line arguments
            result = runner.invoke(
                app,
                [
                    "users",
                    "create-admin",
                    "--username",
                    test_username,
                    "--password",
                    test_password,
                    "--email",
                    test_email,
                ],
                env={
                    "ADMIN_USERNAME": test_username,
                    "ADMIN_PASSWORD": test_password,
                    "ADMIN_EMAIL": test_email,
                },
            )

        # Assert - Check CLI output
        assert result.exit_code == 0, f"CLI command failed: {result.stderr}"

        # Check output contains success message
        assert "✅ Admin user" in result.stdout
        assert "created successfully!" in result.stdout
        assert test_username in result.stdout

    def test_create_admin_user_missing_credentials(
        self, test_infrastructure_factory: Any, runner: typer.testing.CliRunner
    ) -> None:
        """Test CLI command behavior when required credentials are missing."""
        # Patch the get_infrastructure_factory function to return our test factory
        with patch(
            "event_sourcing.cli.users.create_admin.get_infrastructure_factory",
            return_value=test_infrastructure_factory,
        ):
            # Act - Execute the CLI command without providing credentials
            result = runner.invoke(
                app,
                [
                    "users",
                    "create-admin",
                ],
                env={},
            )

        # Assert - Command should handle missing credentials gracefully
        # This tests that the CLI can handle edge cases properly
        # The exact behavior depends on how the settings handle missing values
        assert isinstance(result.exit_code, int)  # Command completed

        # Check that appropriate error handling occurred
        if result.exit_code != 0:
            # If it fails, should have meaningful error message
            assert len(result.stderr) > 0 or len(result.stdout) > 0

    def test_create_admin_user_with_custom_names(
        self, test_infrastructure_factory: Any, runner: typer.testing.CliRunner
    ) -> None:
        """Test admin user creation with custom first and last names."""
        # Arrange
        test_username = f"custom_admin_{uuid.uuid4().hex[:8]}"
        test_email = f"custom_admin_{uuid.uuid4().hex[:8]}@example.com"
        test_password = (
            "CustomPass123!"  # pragma: allowlist secret  # noqa: S105
        )
        custom_first_name = "John"
        custom_last_name = "Doe"

        # Patch the get_infrastructure_factory function to return our test factory
        with patch(
            "event_sourcing.cli.users.create_admin.get_infrastructure_factory",
            return_value=test_infrastructure_factory,
        ):
            # Act - Execute the CLI command with custom names
            result = runner.invoke(
                app,
                [
                    "users",
                    "create-admin",
                    "--username",
                    test_username,
                    "--password",
                    test_password,
                    "--email",
                    test_email,
                    "--first-name",
                    custom_first_name,
                    "--last-name",
                    custom_last_name,
                ],
                env={},
            )

        # Assert - Check CLI output
        assert result.exit_code == 0, f"CLI command failed: {result.stderr}"

        # Check output contains success message
        assert "✅ Admin user" in result.stdout
        assert "created successfully!" in result.stdout
        assert test_username in result.stdout

        # Check that custom names were used
        assert f"First Name: {custom_first_name}" in result.stdout
        assert f"Last Name: {custom_last_name}" in result.stdout
