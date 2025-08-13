"""System tests for user management endpoints.

These tests use a real test database and infrastructure components,
with no mocking. They test the complete flow from API endpoint
to database persistence.
"""

import pytest
from httpx import AsyncClient

# Fixtures are now defined in conftest.py


class TestUserCreation:
    """Test user creation endpoint with real database."""

    @pytest.mark.asyncio
    async def test_create_user_success(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test successful user creation."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "securepassword123",  # pragma: allowlist secret
        }

        # Act
        response = await async_client_with_test_db.post(
            "/v1/users/", json=user_data
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "User created successfully"
        assert "user_id" in response_data
        assert response_data["user_id"] is not None

        # Note: We don't verify the user in the read model here because
        # that would test the projection system, not the user creation endpoint.
        # The projection system has its own unit tests.

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test that creating a user with duplicate username fails."""
        # Arrange - create first user
        user_data = {
            "username": "duplicateuser",
            "email": "user1@example.com",
            "first_name": "First",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        first_response = await async_client_with_test_db.post(
            "/v1/users/", json=user_data
        )
        assert first_response.status_code == 200

        # Act - try to create second user with same username
        duplicate_user_data = {
            "username": "duplicateuser",  # Same username
            "email": "user2@example.com",  # Different email
            "first_name": "Second",
            "last_name": "User",
            "password": "password456",  # pragma: allowlist secret
        }

        second_response = await async_client_with_test_db.post(
            "/v1/users/", json=duplicate_user_data
        )

        # Assert - should fail with conflict error (409)
        assert second_response.status_code == 409
        # The command handler raises UsernameAlreadyExists which gets converted to 409

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test that creating a user with duplicate email fails."""
        # Arrange - create first user
        user_data = {
            "username": "user1",
            "email": "duplicate@example.com",
            "first_name": "First",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        first_response = await async_client_with_test_db.post(
            "/v1/users/", json=user_data
        )
        assert first_response.status_code == 200

        # Act - try to create second user with same email
        duplicate_user_data = {
            "username": "user2",  # Different username
            "email": "duplicate@example.com",  # Same email
            "first_name": "Second",
            "last_name": "User",
            "password": "password456",  # pragma: allowlist secret
        }

        second_response = await async_client_with_test_db.post(
            "/v1/users/", json=duplicate_user_data
        )

        # Assert - should fail with conflict error (409)
        assert second_response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_user_invalid_data(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test user creation with invalid data."""
        # Test missing required fields
        invalid_user_data = {
            "username": "testuser",
            # Missing email
            "first_name": "Test",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        response = await async_client_with_test_db.post(
            "/v1/users/", json=invalid_user_data
        )

        assert response.status_code == 422

        # Test invalid email format
        invalid_email_data = {
            "username": "testuser",
            "email": "invalid-email",
            "first_name": "Test",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        response = await async_client_with_test_db.post(
            "/v1/users/", json=invalid_email_data
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_username_too_short(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test that username must be at least 3 characters."""
        user_data = {
            "username": "ab",  # Too short
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        response = await async_client_with_test_db.post(
            "/v1/users/", json=user_data
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_empty_password(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test that password cannot be empty."""
        user_data = {
            "username": "emptypassuser",
            "email": "emptypass@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "",  # Empty password
        }

        response = await async_client_with_test_db.post(
            "/v1/users/", json=user_data
        )

        assert response.status_code == 422
