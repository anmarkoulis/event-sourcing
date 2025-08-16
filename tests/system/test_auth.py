"""System tests for authentication endpoints.

These tests use a real test database and infrastructure components,
with no mocking. They test the complete flow from API endpoint
to database persistence.
"""

import pytest
from httpx import AsyncClient


class TestLoginEndpoint:
    """Test the login endpoint with real database."""

    @pytest.mark.asyncio
    async def test_login_success_admin(
        self, async_client_with_test_db: AsyncClient, admin_user: dict
    ) -> None:
        """Test successful admin login."""
        # Arrange
        login_data = {
            "username": admin_user["username"],
            "password": admin_user["password"],
        }

        # Act
        response = await async_client_with_test_db.post(
            "/v1/auth/login/", json=login_data
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert "access_token" in response_data
        assert "token_type" in response_data
        assert "user" in response_data

        # Check token type
        assert response_data["token_type"] == "bearer"  # noqa: S105

        # Check access token format (JWT tokens start with "eyJ")
        access_token = response_data["access_token"]
        assert access_token.startswith("eyJ")
        assert len(access_token) > 50

        # Check user data
        user = response_data["user"]
        assert user["username"] == admin_user["username"]
        assert user["email"] == admin_user["email"]
        assert user["first_name"] == admin_user["first_name"]
        assert user["last_name"] == admin_user["last_name"]
        assert user["role"] == admin_user["role"]

    @pytest.mark.asyncio
    async def test_login_success_regular_user(
        self, async_client_with_test_db: AsyncClient, regular_user: dict
    ) -> None:
        """Test successful regular user login."""
        # Arrange
        login_data = {
            "username": regular_user["username"],
            "password": regular_user["password"],
        }

        # Act
        response = await async_client_with_test_db.post(
            "/v1/auth/login/", json=login_data
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert "access_token" in response_data
        assert "token_type" in response_data
        assert "user" in response_data

        # Check token type
        assert response_data["token_type"] == "bearer"  # noqa: S105

        # Check access token format
        access_token = response_data["access_token"]
        assert access_token.startswith("eyJ")
        assert len(access_token) > 50

        # Check user data
        user = response_data["user"]
        assert user["username"] == regular_user["username"]
        assert user["email"] == regular_user["email"]
        assert user["first_name"] == regular_user["first_name"]
        assert user["last_name"] == regular_user["last_name"]
        assert user["role"] == regular_user["role"]

    @pytest.mark.asyncio
    async def test_login_invalid_username(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test login with invalid username."""
        # Arrange
        login_data = {
            "username": "nonexistentuser",
            "password": "password123",  # pragma: allowlist secret
        }

        # Act
        response = await async_client_with_test_db.post(
            "/v1/auth/login/", json=login_data
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert response_data["message"] == "Incorrect username or password"

        # Note: The application doesn't set WWW-Authenticate headers in the custom exception handler

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self, async_client_with_test_db: AsyncClient, admin_user: dict
    ) -> None:
        """Test login with invalid password."""
        # Arrange
        login_data = {
            "username": admin_user["username"],
            "password": "wrongpassword",  # pragma: allowlist secret
        }

        # Act
        response = await async_client_with_test_db.post(
            "/v1/auth/login/", json=login_data
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert response_data["message"] == "Incorrect username or password"

        # Note: The application doesn't set WWW-Authenticate headers in the custom exception handler

    @pytest.mark.asyncio
    async def test_login_missing_username(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test login with missing username."""
        # Arrange
        login_data = {
            "password": "password123",  # pragma: allowlist secret
        }

        # Act
        response = await async_client_with_test_db.post(
            "/v1/auth/login/", json=login_data
        )

        # Assert
        assert response.status_code == 422
        response_data = response.json()

        # Check validation error structure
        assert "details" in response_data

        # Check that the missing field is reported
        details = response_data["details"]
        assert isinstance(details, list)

        # Find the username field error
        username_error = next(
            (
                error
                for error in details
                if error.get("loc") and "username" in error["loc"]
            ),
            None,
        )
        assert username_error is not None
        assert "field required" in username_error.get("msg", "").lower()

    @pytest.mark.asyncio
    async def test_login_missing_password(
        self, async_client_with_test_db: AsyncClient, admin_user: dict
    ) -> None:
        """Test login with missing password."""
        # Arrange
        login_data = {
            "username": admin_user["username"],
        }

        # Act
        response = await async_client_with_test_db.post(
            "/v1/auth/login/", json=login_data
        )

        # Assert
        assert response.status_code == 422
        response_data = response.json()

        # Check validation error structure
        assert "details" in response_data

        # Check that the missing field is reported
        details = response_data["details"]
        assert isinstance(details, list)

        # Find the password field error
        password_error = next(
            (
                error
                for error in details
                if error.get("loc") and "password" in error["loc"]
            ),
            None,
        )
        assert password_error is not None
        assert "field required" in password_error.get("msg", "").lower()

    @pytest.mark.asyncio
    async def test_login_empty_username(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test login with empty username."""
        # Arrange
        login_data = {
            "username": "",
            "password": "password123",  # pragma: allowlist secret
        }

        # Act
        response = await async_client_with_test_db.post(
            "/v1/auth/login/", json=login_data
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert response_data["message"] == "Incorrect username or password"

        # Note: The application doesn't set WWW-Authenticate headers in the custom exception handler

    @pytest.mark.asyncio
    async def test_login_empty_password(
        self, async_client_with_test_db: AsyncClient, admin_user: dict
    ) -> None:
        """Test login with empty password."""
        # Arrange
        login_data = {
            "username": admin_user["username"],
            "password": "",
        }

        # Act
        response = await async_client_with_test_db.post(
            "/v1/auth/login/", json=login_data
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert response_data["message"] == "Incorrect username or password"

        # Note: The application doesn't set WWW-Authenticate headers in the custom exception handler

    @pytest.mark.asyncio
    async def test_login_invalid_json(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test login with invalid JSON."""
        # Act
        response = await async_client_with_test_db.post(
            "/v1/auth/login/",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Assert
        assert response.status_code == 422
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "Request Validation Error"
        assert "details" in response_data

    @pytest.mark.asyncio
    async def test_login_wrong_content_type(
        self, async_client_with_test_db: AsyncClient
    ) -> None:
        """Test login with wrong content type."""
        # Act
        response = await async_client_with_test_db.post(
            "/v1/auth/login/",
            content=b"invalid bytes content",
            headers={"Content-Type": "application/octet-stream"},
        )

        # Assert
        assert response.status_code == 422
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "Request Validation Error"
        assert "Request validation failed" in response_data["message"]
