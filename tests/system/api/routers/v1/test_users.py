"""System tests for user management endpoints.

These tests use a real test database and infrastructure components,
with no mocking. They test the complete flow from API endpoint
to database persistence.
"""

from typing import Any

import pytest
from httpx import AsyncClient

# Fixtures are now defined in conftest.py


class TestUserCreation:
    """Test user creation endpoint with real database."""

    @pytest.mark.asyncio
    async def test_create_user_unauthorized_no_jwt(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        """Test that creating a user without JWT returns 401."""
        # Arrange
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        # Act
        response = await unauthenticated_client.post(
            "/v1/users/", json=user_data
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "not authenticated" in response_data["message"].lower()

    @pytest.mark.asyncio
    async def test_create_user_forbidden_regular_user(
        self, user_client: AsyncClient
    ) -> None:
        """Test that regular users cannot create users (403)."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "securepassword123",  # pragma: allowlist secret
        }

        # Act
        response = await user_client.post("/v1/users/", json=user_data)

        # Assert
        assert response.status_code == 403
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "insufficient permissions" in response_data["message"].lower()

    @pytest.mark.asyncio
    async def test_create_user_success(
        self, admin_client: AsyncClient
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
        response = await admin_client.post("/v1/users/", json=user_data)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert "message" in response_data
        assert "user_id" in response_data

        # Check message content
        assert response_data["message"] == "User created successfully"

        # Check user_id is a valid UUID
        import uuid

        try:
            user_id = uuid.UUID(response_data["user_id"])
            assert user_id is not None
        except ValueError:
            pytest.fail("user_id is not a valid UUID")

        # Note: We don't verify the user in the read model here because
        # that would test the projection system, not the user creation endpoint.
        # The projection system has its own unit tests.

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(
        self, admin_client: AsyncClient
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

        first_response = await admin_client.post("/v1/users/", json=user_data)
        assert first_response.status_code == 200

        # Act - try to create second user with same username
        duplicate_user_data = {
            "username": "duplicateuser",  # Same username
            "email": "user2@example.com",  # Different email
            "first_name": "Second",
            "last_name": "User",
            "password": "password456",  # pragma: allowlist secret
        }

        second_response = await admin_client.post(
            "/v1/users/", json=duplicate_user_data
        )

        # Assert - should fail with conflict error (409)
        assert second_response.status_code == 409
        response_data = second_response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert "details" in response_data

        # Check error type
        assert response_data["error"] == "Resource Conflict"

        # Check conflict details
        assert "username" in response_data["details"]
        assert response_data["details"]["username"] == "duplicateuser"

        # The command handler raises UsernameAlreadyExists which gets converted to 409

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self, admin_client: AsyncClient
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

        first_response = await admin_client.post("/v1/users/", json=user_data)
        assert first_response.status_code == 200

        # Act - try to create second user with same email
        duplicate_user_data = {
            "username": "user2",  # Different username
            "email": "duplicate@example.com",  # Same email
            "first_name": "Second",
            "last_name": "User",
            "password": "password456",  # pragma: allowlist secret
        }

        second_response = await admin_client.post(
            "/v1/users/", json=duplicate_user_data
        )

        # Assert - should fail with conflict error (409)
        assert second_response.status_code == 409
        response_data = second_response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert "details" in response_data

        # Check error type
        assert response_data["error"] == "Resource Conflict"

        # Check conflict details
        assert "email" in response_data["details"]
        assert response_data["details"]["email"] == "duplicate@example.com"

    @pytest.mark.asyncio
    async def test_create_user_invalid_data(
        self, admin_client: AsyncClient
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

        response = await admin_client.post(
            "/v1/users/", json=invalid_user_data
        )

        # Assert - should fail with validation error (422)
        assert response.status_code == 422
        response_data = response.json()

        # Check validation error structure
        assert "details" in response_data

        # Check that the missing field is reported
        details = response_data["details"]
        assert isinstance(details, list)

        # Find the email field error
        email_error = next(
            (
                error
                for error in details
                if error.get("loc") and "email" in error["loc"]
            ),
            None,
        )
        assert email_error is not None
        assert "field required" in email_error.get("msg", "").lower()

    @pytest.mark.asyncio
    async def test_create_user_username_too_short(
        self, admin_client: AsyncClient
    ) -> None:
        """Test that username must be at least 3 characters."""
        user_data = {
            "username": "ab",  # Too short
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        response = await admin_client.post("/v1/users/", json=user_data)

        # Assert - should fail with validation error (422)
        assert response.status_code == 422
        response_data = response.json()

        # Check validation error structure
        assert "details" in response_data

        # Check that the username length error is reported
        details = response_data["details"]
        # For domain validation errors, details is a dict with field info
        assert isinstance(details, dict)

        # Check that username validation error is present
        assert "username" in details
        assert "min_length" in details
        assert details["min_length"] == 3

    @pytest.mark.asyncio
    async def test_create_user_empty_password(
        self, admin_client: AsyncClient
    ) -> None:
        """Test that password cannot be empty."""
        user_data = {
            "username": "emptypassuser",
            "email": "emptypass@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "",  # Empty password
        }

        response = await admin_client.post("/v1/users/", json=user_data)

        # Assert - should fail with validation error (422)
        assert response.status_code == 422
        response_data = response.json()

        # Check validation error structure
        assert "details" in response_data

        # Check that the password error is reported
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
        assert "String should have at least 1 character" in password_error.get(
            "msg", ""
        )


class TestUserListing:
    """Test user listing endpoint with real database."""

    @pytest.mark.asyncio
    async def test_list_users_unauthorized_no_jwt(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        """Test that listing users without JWT returns 401."""
        # Act
        response = await unauthenticated_client.get("/v1/users/")

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "not authenticated" in response_data["message"].lower()

    @pytest.mark.asyncio
    async def test_list_users_success_regular_user(
        self, user_client: AsyncClient
    ) -> None:
        """Test that regular users can list users (they have user:read permission)."""
        # Act
        response = await user_client.get("/v1/users/")

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert "results" in response_data
        assert "count" in response_data
        assert "page" in response_data
        assert "page_size" in response_data
        assert isinstance(response_data["results"], list)
        assert isinstance(response_data["count"], int)
        assert isinstance(response_data["page"], int)
        assert isinstance(response_data["page_size"], int)

    @pytest.mark.asyncio
    async def test_list_users_success_admin(
        self, admin_client: AsyncClient
    ) -> None:
        """Test successful user listing as admin."""
        # Arrange - create exactly 3 users for predictable testing
        users_data = [
            {
                "username": "listuser1",
                "email": "list1@example.com",
                "first_name": "List",
                "last_name": "User1",
                "password": "password123",  # pragma: allowlist secret
            },
            {
                "username": "listuser2",
                "email": "list2@example.com",
                "first_name": "List",
                "last_name": "User2",
                "password": "password456",  # pragma: allowlist secret
            },
            {
                "username": "listuser3",
                "email": "list3@example.com",
                "first_name": "List",
                "last_name": "User3",
                "password": "password789",  # pragma: allowlist secret
            },
        ]

        created_user_ids = []
        for user_data in users_data:
            response = await admin_client.post("/v1/users/", json=user_data)
            assert response.status_code == 200
            created_user_ids.append(response.json()["user_id"])

        # Act - list users
        response = await admin_client.get("/v1/users/")

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check the actual response structure
        print(f"List users response: {response_data}")

        # Verify the response structure matches ListUsersResponse
        assert "results" in response_data
        assert "count" in response_data
        assert "page" in response_data
        assert "page_size" in response_data
        assert "next" in response_data
        assert "previous" in response_data

        # Check data types
        assert isinstance(response_data["count"], int)
        assert isinstance(response_data["page"], int)
        assert isinstance(response_data["page_size"], int)
        assert isinstance(response_data["results"], list)

        # With a fresh database and 3 users created in this test, we should have 4 users total
        # (admin from setup + 3 users created in this test)
        assert response_data["count"] == 4
        assert len(response_data["results"]) == 4

        # Check that our created users are in the results
        found_usernames = [
            user["username"] for user in response_data["results"]
        ]
        assert "listuser1" in found_usernames
        assert "listuser2" in found_usernames
        assert "listuser3" in found_usernames

        # Check user structure in results
        for user in response_data["results"]:
            assert "id" in user
            assert "username" in user
            assert "email" in user
            assert "first_name" in user
            assert "last_name" in user
            assert "created_at" in user
            assert "updated_at" in user

    @pytest.mark.asyncio
    async def test_list_users_pagination(
        self, admin_client: AsyncClient
    ) -> None:
        """Test user listing pagination."""
        # Arrange - create exactly 15 users to test pagination properly
        users_to_create = 15
        created_users = []

        for i in range(users_to_create):
            user_data = {
                "username": f"paginationuser{i:02d}",
                "email": f"pagination{i:02d}@example.com",
                "first_name": f"Pagination{i:02d}",
                "last_name": "User",
                "password": "password123",  # pragma: allowlist secret
            }

            response = await admin_client.post("/v1/users/", json=user_data)
            assert response.status_code == 200
            created_users.append(response.json()["user_id"])

        # Act - test pagination with page_size=5
        response = await admin_client.get("/v1/users/?page=1&page_size=5")

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check pagination fields
        assert response_data["page"] == 1
        assert response_data["page_size"] == 5

        # Check data types
        assert isinstance(response_data["page"], int)
        assert isinstance(response_data["page_size"], int)
        assert isinstance(response_data["count"], int)
        assert isinstance(response_data["results"], list)

        # Check pagination logic - we created exactly 15 users plus admin from setup
        assert response_data["count"] == 16
        assert len(response_data["results"]) == 5

        # Check pagination links
        assert response_data["next"] is not None  # Should have next page
        assert response_data["previous"] is None  # Page 1 has no previous

        # Test page 2
        response_page2 = await admin_client.get(
            "/v1/users/?page=2&page_size=5"
        )
        assert response_page2.status_code == 200
        page2_data = response_page2.json()

        assert page2_data["page"] == 2
        assert page2_data["page_size"] == 5
        assert page2_data["count"] == 16
        assert len(page2_data["results"]) == 5

        # Check pagination links for page 2
        assert page2_data["next"] is not None  # Should have next page
        assert page2_data["previous"] is not None  # Should have previous page

        # Test page 3 (should have next page since we have 16 users total)
        response_page3 = await admin_client.get(
            "/v1/users/?page=3&page_size=5"
        )
        assert response_page3.status_code == 200
        page3_data = response_page3.json()

        assert page3_data["page"] == 3
        assert page3_data["page_size"] == 5
        assert page3_data["count"] == 16
        assert len(page3_data["results"]) == 5

        # Check pagination links for page 3 (should have next page since there are more users)
        assert page3_data["next"] is not None  # Should have next page (page 4)
        assert page3_data["previous"] is not None  # Should have previous page

        # Test page 4 (last page with 1 user)
        response_page4 = await admin_client.get(
            "/v1/users/?page=4&page_size=5"
        )
        assert response_page4.status_code == 200
        page4_data = response_page4.json()

        assert page4_data["page"] == 4
        assert page4_data["page_size"] == 5
        assert page4_data["count"] == 16
        assert len(page4_data["results"]) == 1

        # Check pagination links for page 4 (last page)
        assert page4_data["next"] is None  # Last page has no next
        assert page4_data["previous"] is not None  # Should have previous page

        # Verify that different pages return different users
        page1_usernames = [
            user["username"] for user in response_data["results"]
        ]
        page2_usernames = [user["username"] for user in page2_data["results"]]
        page3_usernames = [user["username"] for user in page3_data["results"]]

        # All usernames should be unique across pages
        all_usernames = page1_usernames + page2_usernames + page3_usernames
        assert len(all_usernames) == len(set(all_usernames))  # No duplicates

        # Verify we have all 15 users across the 3 pages
        assert len(all_usernames) == 15

    @pytest.mark.asyncio
    async def test_list_users_filtering(
        self, admin_client: AsyncClient
    ) -> None:
        """Test user listing with filters."""
        # Arrange - create users with specific patterns for filtering
        filter_users_data = [
            {
                "username": "filteruser1",
                "email": "filter1@example.com",
                "first_name": "Filter",
                "last_name": "User1",
                "password": "password123",  # pragma: allowlist secret
            },
            {
                "username": "filteruser2",
                "email": "filter2@example.com",
                "first_name": "Filter",
                "last_name": "User2",
                "password": "password456",  # pragma: allowlist secret
            },
            {
                "username": "otheruser",
                "email": "other@example.com",
                "first_name": "Other",
                "last_name": "User",
                "password": "password789",  # pragma: allowlist secret
            },
        ]

        for user_data in filter_users_data:
            response = await admin_client.post("/v1/users/", json=user_data)
            assert response.status_code == 200

        # Act - list users with username filter
        response = await admin_client.get("/v1/users/?username=filteruser")

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert "results" in response_data
        assert "count" in response_data

        # Check data types
        assert isinstance(response_data["count"], int)
        assert isinstance(response_data["results"], list)

        # We should have exactly 2 users matching the filter
        assert response_data["count"] == 2

        # All returned users should have username containing "filteruser"
        for user in response_data["results"]:
            assert "username" in user
            assert "filteruser" in user["username"]

        # Verify that filtering actually worked
        found_usernames = [
            user["username"] for user in response_data["results"]
        ]
        assert "filteruser1" in found_usernames
        assert "filteruser2" in found_usernames
        assert (
            "otheruser" not in found_usernames
        )  # Should not be in filtered results


class TestUserRetrieval:
    """Test user retrieval endpoints with real database."""

    @pytest.mark.asyncio
    async def test_get_user_unauthorized_no_jwt(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        """Test that getting a user without JWT returns 401."""
        # Act
        response = await unauthenticated_client.get(
            "/v1/users/11111111-1111-1111-1111-111111111111/"
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "not authenticated" in response_data["message"].lower()

    @pytest.mark.asyncio
    async def test_get_user_success_regular_user(
        self, admin_client: AsyncClient, user_client: AsyncClient
    ) -> None:
        """Test that regular users can get user information (they have user:read permission)."""
        # Arrange - create a user as admin first
        user_data = {
            "username": "readableuser",
            "email": "readable@example.com",
            "first_name": "Readable",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200

        user_id = create_response.json()["user_id"]

        # Act - try to get the user with regular user permissions (should succeed with 200)
        response = await user_client.get(f"/v1/users/{user_id}/")

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert "user" in response_data
        user = response_data["user"]

        # Check user data matches what we created
        assert user["username"] == "readableuser"
        assert user["email"] == "readable@example.com"
        assert user["first_name"] == "Readable"
        assert user["last_name"] == "User"

    @pytest.mark.asyncio
    async def test_get_user_success(self, admin_client: AsyncClient) -> None:
        """Test successful user retrieval."""
        # Arrange - create a user
        user_data = {
            "username": "getuser",
            "email": "get@example.com",
            "first_name": "Get",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200

        user_id = create_response.json()["user_id"]

        # Act - get the user
        response = await admin_client.get(f"/v1/users/{user_id}/")

        # Assert
        # With synchronous event handling, the read model is updated immediately
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert "user" in response_data
        user = response_data["user"]

        # Check user data matches what we created
        assert user["username"] == "getuser"
        assert user["email"] == "get@example.com"
        assert user["first_name"] == "Get"
        assert user["last_name"] == "User"

        # Check that all required fields are present
        assert "id" in user
        assert "created_at" in user
        assert "updated_at" in user

        # Check data types
        assert isinstance(user["id"], str)
        assert isinstance(user["username"], str)
        assert isinstance(user["email"], str)
        assert isinstance(user["first_name"], str)
        assert isinstance(user["last_name"], str)
        assert isinstance(user["created_at"], str)
        assert isinstance(user["updated_at"], str)

        # Verify the ID matches
        assert user["id"] == user_id

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, admin_client: AsyncClient) -> None:
        """Test getting a non-existent user."""
        # Act - try to get a non-existent user
        response = await admin_client.get(
            "/v1/users/11111111-1111-1111-1111-111111111111/"
        )

        # Assert
        assert response.status_code == 404
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert "type" in response_data

        # Check error type - this is an HTTP exception, not a domain exception
        assert response_data["error"] == "HTTP Error"
        assert response_data["type"] == "HTTPException"

    @pytest.mark.asyncio
    async def test_get_user_history_success(
        self, admin_client: AsyncClient, freezer: Any
    ) -> None:
        """Test successful user history retrieval."""
        # Arrange - create a user at a specific time
        user_data = {
            "username": "historyuser",
            "email": "history@example.com",
            "first_name": "History",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        # Create user at a specific time
        with freezer("2025-08-14 06:00:00"):
            create_response = await admin_client.post(
                "/v1/users/", json=user_data
            )
            assert create_response.status_code == 200
            user_id = create_response.json()["user_id"]

        # Act - get user history (use a timestamp after user creation)
        with freezer("2025-08-14 06:30:00"):
            response = await admin_client.get(
                f"/v1/users/{user_id}/history/?timestamp=2025-08-14T06:30:00"
            )

        # Assert
        # With synchronous event handling, the read model is updated immediately
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure - the history endpoint returns the user state at the specified timestamp
        assert "id" in response_data
        assert "username" in response_data
        assert "email" in response_data
        assert "first_name" in response_data
        assert "last_name" in response_data

        # Check user data matches what we created
        assert response_data["username"] == "historyuser"
        assert response_data["email"] == "history@example.com"
        assert response_data["first_name"] == "History"
        assert response_data["last_name"] == "User"

        # Check data types
        assert isinstance(response_data["id"], str)
        assert isinstance(response_data["username"], str)
        assert isinstance(response_data["email"], str)
        assert isinstance(response_data["first_name"], str)
        assert isinstance(response_data["last_name"], str)

        # Verify the ID matches
        assert response_data["id"] == user_id


class TestUserUpdate:
    """Test user update endpoints with real database."""

    @pytest.mark.asyncio
    async def test_update_user_unauthorized_no_jwt(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        """Test that updating a user without JWT returns 401."""
        # Arrange
        update_data = {"first_name": "Updated", "last_name": "Name"}

        # Act
        response = await unauthenticated_client.put(
            "/v1/users/11111111-1111-1111-1111-111111111111/", json=update_data
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "not authenticated" in response_data["message"].lower()

    @pytest.mark.asyncio
    async def test_update_user_forbidden_regular_user(
        self, admin_client: AsyncClient, user_client: AsyncClient
    ) -> None:
        """Test that regular users cannot update other users (403)."""
        # Arrange - create a user as admin first
        user_data = {
            "username": "updateforbiddenuser",
            "email": "updateforbidden@example.com",
            "first_name": "Update",
            "last_name": "Forbidden",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200

        user_id = create_response.json()["user_id"]

        # Act - try to update the user with regular user permissions (should fail with 403)
        # This tests the require_update_user_permission function and the branch where
        # regular users try to update other users' data
        update_data = {"first_name": "Updated", "last_name": "Name"}
        response = await user_client.put(
            f"/v1/users/{user_id}/", json=update_data
        )

        # Assert
        assert response.status_code == 403
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "insufficient permissions" in response_data["message"].lower()
        # This should test the specific error message from require_update_specific_user_permission
        assert (
            "only update your own user data"
            in response_data["message"].lower()
        )

    @pytest.mark.asyncio
    async def test_update_user_regular_user_own_data_success(
        self, admin_client: AsyncClient, user_client: AsyncClient
    ) -> None:
        """Test that regular users can update their own data successfully."""
        # Arrange - create a user
        user_data = {
            "username": "ownuser",
            "email": "ownuser@example.com",
            "first_name": "Own",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200

        user_id = create_response.json()["user_id"]

        # Get the user's own JWT token by logging in
        login_response = await user_client.post(
            "/v1/auth/login/",
            json={
                "username": "ownuser",
                "password": "password123",  # pragma: allowlist secret
            },
        )
        assert login_response.status_code == 200
        own_token = login_response.json()["access_token"]

        # Create a client with the user's own token
        import httpx

        own_client = httpx.AsyncClient(
            transport=user_client._transport,
            base_url=user_client.base_url,
            headers={"Authorization": f"Bearer {own_token}"},
        )

        # Act - try to update own data (should succeed)
        # This tests the branch where users update their own data in require_update_specific_user_permission
        update_data = {"first_name": "MyOwn", "last_name": "Data"}
        response = await own_client.put(
            f"/v1/users/{user_id}/", json=update_data
        )

        # Assert - should succeed because users can update their own data
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert response_data["message"] == "User updated successfully"

        # Clean up
        await own_client.aclose()

    @pytest.mark.asyncio
    async def test_update_user_admin_can_update_any_user(
        self, admin_client: AsyncClient
    ) -> None:
        """Test that admin users can update any user's data."""
        # Arrange - create a user
        user_data = {
            "username": "adminupdateuser",
            "email": "adminupdate@example.com",
            "first_name": "AdminUpdate",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200

        user_id = create_response.json()["user_id"]

        # Act - admin updates the user (should succeed)
        # This tests the admin branch in require_update_specific_user_permission
        # where admin has user:delete scope (admin role)
        update_data = {"first_name": "Admin", "last_name": "Updated"}
        response = await admin_client.put(
            f"/v1/users/{user_id}/", json=update_data
        )

        # Assert - should succeed because admin has user:delete scope (admin role)
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert response_data["message"] == "User updated successfully"

    @pytest.mark.asyncio
    async def test_update_user_success(
        self, admin_client: AsyncClient
    ) -> None:
        """Test successful user update."""
        # Arrange - create a user
        user_data = {
            "username": "updateuser",
            "email": "update@example.com",
            "first_name": "Update",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200

        user_id = create_response.json()["user_id"]

        # Act - update the user
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
        }

        response = await admin_client.put(
            f"/v1/users/{user_id}/", json=update_data
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert "message" in response_data
        assert response_data["message"] == "User updated successfully"

        # Verify the update by getting the user again
        get_response = await admin_client.get(f"/v1/users/{user_id}/")
        assert get_response.status_code == 200

        updated_user = get_response.json()["user"]

        # Check that the fields were updated
        assert updated_user["first_name"] == "Updated"
        assert updated_user["last_name"] == "Name"
        assert updated_user["email"] == "updated@example.com"

        # Check that username remains unchanged
        assert updated_user["username"] == "updateuser"

        # Check that timestamps are present
        assert "created_at" in updated_user
        assert "updated_at" in updated_user

    @pytest.mark.asyncio
    async def test_update_user_not_found(
        self, admin_client: AsyncClient
    ) -> None:
        """Test updating a non-existent user."""
        # Act - try to update a non-existent user
        update_data = {"first_name": "Updated", "last_name": "Name"}

        response = await admin_client.put(
            "/v1/users/11111111-1111-1111-1111-111111111111/", json=update_data
        )

        # Assert - should fail with 404 since user doesn't exist
        assert response.status_code == 404
        response_data = response.json()
        assert "error" in response_data
        assert response_data["error"] == "Resource Not Found"
        assert (
            "User 11111111-1111-1111-1111-111111111111 not found"
            in response_data["message"]
        )

    @pytest.mark.asyncio
    async def test_update_user_invalid_data(
        self, admin_client: AsyncClient
    ) -> None:
        """Test user update with invalid data."""
        # Arrange - create a user
        user_data = {
            "username": "updateinvaliduser",
            "email": "updateinvalid@example.com",
            "first_name": "Update",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200

        user_id = create_response.json()["user_id"]

        # Act - try to update with invalid email
        invalid_update_data = {
            "email": "invalid-email"  # Invalid email format
        }

        response = await admin_client.put(
            f"/v1/users/{user_id}/", json=invalid_update_data
        )

        # Assert - should fail with validation error (422)
        assert response.status_code == 422
        response_data = response.json()

        # Check validation error structure
        assert "details" in response_data

        # Check that the email format error is reported
        details = response_data["details"]
        assert isinstance(details, list)

        # Find the email field error
        email_error = next(
            (
                error
                for error in details
                if error.get("loc") and "email" in error["loc"]
            ),
            None,
        )
        assert email_error is not None
        assert "valid email" in email_error.get("msg", "").lower()

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_other_user_data(
        self, user_client: AsyncClient, admin_client: AsyncClient
    ) -> None:
        """Test that regular users cannot update other users' data."""
        # Arrange - create a user
        user_data = {
            "username": "permissiontestuser",
            "email": "permissiontest@example.com",
            "first_name": "Permission",
            "last_name": "Test",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200
        user_id = create_response.json()["user_id"]

        # Act - try to update the user with regular user permissions (should fail)
        # This tests that regular users cannot update other users' data
        update_data = {"first_name": "Updated", "last_name": "Name"}
        response = await user_client.put(
            f"/v1/users/{user_id}/", json=update_data
        )

        # Assert - should fail because regular users can only update their own data
        assert response.status_code == 403
        response_data = response.json()
        assert "error" in response_data
        assert "message" in response_data
        assert "only update your own user data" in response_data["message"]

    @pytest.mark.asyncio
    async def test_regular_user_update_own_data_success(
        self, user_client: AsyncClient, admin_client: AsyncClient
    ) -> None:
        """Test that regular users can update their own data."""
        # Arrange - create a user
        user_data = {
            "username": "ownuser",
            "email": "ownuser@example.com",
            "first_name": "Own",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200
        user_id = create_response.json()["user_id"]

        # Get the user's own JWT token by logging in
        login_response = await user_client.post(
            "/v1/auth/login/",
            json={
                "username": "ownuser",
                "password": "password123",  # pragma: allowlist secret
            },
        )
        assert login_response.status_code == 200
        own_token = login_response.json()["access_token"]

        # Create a client with the user's own token
        import httpx

        own_client = httpx.AsyncClient(
            transport=user_client._transport,
            base_url=user_client.base_url,
            headers={"Authorization": f"Bearer {own_token}"},
        )

        # Act - try to update own data (should succeed)
        update_data = {"first_name": "MyOwn", "last_name": "Data"}
        response = await own_client.put(
            f"/v1/users/{user_id}/", json=update_data
        )

        # Assert - should succeed because users can update their own data
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert response_data["message"] == "User updated successfully"

        # Clean up
        await own_client.aclose()

    @pytest.mark.asyncio
    async def test_admin_update_any_user_success(
        self, admin_client: AsyncClient
    ) -> None:
        """Test that admin users can update any user's data."""
        # Arrange - create a user
        user_data = {
            "username": "anyuser",
            "email": "anyuser@example.com",
            "first_name": "Any",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200
        user_id = create_response.json()["user_id"]

        # Act - admin updates the user (should succeed)
        update_data = {"first_name": "Admin", "last_name": "Updated"}
        response = await admin_client.put(
            f"/v1/users/{user_id}/", json=update_data
        )

        # Assert - should succeed because admin has permissions
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert response_data["message"] == "User updated successfully"

        # Verify the update by getting the user again
        get_response = await admin_client.get(f"/v1/users/{user_id}/")
        assert get_response.status_code == 200

        updated_user = get_response.json()["user"]
        assert updated_user["first_name"] == "Admin"
        assert updated_user["last_name"] == "Updated"

    @pytest.mark.asyncio
    async def test_admin_update_own_data_success(
        self, admin_client: AsyncClient
    ) -> None:
        """Test that admin users can update their own data."""
        # Arrange - create an admin user
        admin_data = {
            "username": "adminown",
            "email": "adminown@example.com",
            "first_name": "Admin",
            "last_name": "Own",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post(
            "/v1/users/", json=admin_data
        )
        assert create_response.status_code == 200
        admin_id = create_response.json()["user_id"]

        # Act - admin updates their own data (should succeed)
        update_data = {"first_name": "MyOwn", "last_name": "AdminData"}
        response = await admin_client.put(
            f"/v1/users/{admin_id}/", json=update_data
        )

        # Assert - should succeed because admins can update their own data
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert response_data["message"] == "User updated successfully"

        # Verify the update by getting the user again
        get_response = await admin_client.get(f"/v1/users/{admin_id}/")
        assert get_response.status_code == 200

        updated_user = get_response.json()["user"]
        assert updated_user["first_name"] == "MyOwn"
        assert updated_user["last_name"] == "AdminData"


class TestPasswordChange:
    """Test password change endpoint with real database."""

    @pytest.mark.asyncio
    async def test_change_password_unauthorized_no_jwt(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        """Test that changing password without JWT returns 401."""
        # Arrange
        password_data = {
            "current_password": "oldpassword123",  # pragma: allowlist secret
            "new_password": "newpassword456",  # pragma: allowlist secret
        }

        # Act
        response = await unauthenticated_client.put(
            "/v1/users/11111111-1111-1111-1111-111111111111/password/",
            json=password_data,
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "not authenticated" in response_data["message"].lower()

    @pytest.mark.asyncio
    async def test_change_password_forbidden_regular_user(
        self, admin_client: AsyncClient, user_client: AsyncClient
    ) -> None:
        """Test that regular users cannot change passwords (403)."""
        # Arrange - create a user as admin first
        user_data = {
            "username": "passwordforbiddenuser",
            "email": "passwordforbidden@example.com",
            "first_name": "Password",
            "last_name": "Forbidden",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200

        user_id = create_response.json()["user_id"]

        # Act - try to change password with regular user permissions (should fail with 403)
        password_data = {
            "current_password": "password123",  # pragma: allowlist secret
            "new_password": "newpassword456",  # pragma: allowlist secret
        }
        response = await user_client.put(
            f"/v1/users/{user_id}/password/", json=password_data
        )

        # Assert
        assert response.status_code == 403
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "insufficient permissions" in response_data["message"].lower()

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, admin_client: AsyncClient
    ) -> None:
        """Test successful password change."""
        # Arrange - create a user
        user_data = {
            "username": "passworduser",
            "email": "password@example.com",
            "first_name": "Password",
            "last_name": "User",
            "password": "oldpassword123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200

        user_id = create_response.json()["user_id"]

        # Act - change password
        password_data = {
            "current_password": "oldpassword123",  # pragma: allowlist secret
            "new_password": "newpassword456",  # pragma: allowlist secret
        }

        response = await admin_client.put(
            f"/v1/users/{user_id}/password/", json=password_data
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert "message" in response_data
        assert response_data["message"] == "Password changed successfully"

        # Verify the password change by getting the user again
        get_response = await admin_client.get(f"/v1/users/{user_id}/")
        assert get_response.status_code == 200

        updated_user = get_response.json()["user"]

        # Check that the user still exists and other fields are unchanged
        assert updated_user["username"] == "passworduser"
        assert updated_user["email"] == "password@example.com"
        assert updated_user["first_name"] == "Password"
        assert updated_user["last_name"] == "User"

        # Check that timestamps are present
        assert "created_at" in updated_user
        assert "updated_at" in updated_user

        # Note: We can't verify the actual password hash since it's not exposed in the read model
        # The password change is verified by the successful response and the fact that
        # the user still exists and can be retrieved

    @pytest.mark.asyncio
    async def test_change_password_not_found(
        self, admin_client: AsyncClient
    ) -> None:
        """Test changing password for non-existent user."""
        # Act - try to change password for non-existent user
        password_data = {
            "current_password": "oldpassword123",  # pragma: allowlist secret
            "new_password": "newpassword456",  # pragma: allowlist secret
        }

        response = await admin_client.put(
            "/v1/users/11111111-1111-1111-1111-111111111111/password/",
            json=password_data,
        )

        # Assert - should fail with 404 since user doesn't exist
        assert response.status_code == 404
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "Resource Not Found"
        assert (
            "user" in response_data["message"].lower()
            and "not found" in response_data["message"].lower()
        )


class TestUserDeletion:
    """Test user deletion endpoint with real database."""

    @pytest.mark.asyncio
    async def test_delete_user_unauthorized_no_jwt(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        """Test that deleting a user without JWT returns 401."""
        # Act
        response = await unauthenticated_client.delete(
            "/v1/users/11111111-1111-1111-1111-111111111111/"
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "not authenticated" in response_data["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_user_forbidden_regular_user(
        self, user_client: AsyncClient
    ) -> None:
        """Test that regular users cannot delete users (403)."""
        # Act
        response = await user_client.delete(
            "/v1/users/11111111-1111-1111-1111-111111111111/"
        )

        # Assert
        assert response.status_code == 403
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "insufficient permissions" in response_data["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_user_success(
        self, admin_client: AsyncClient
    ) -> None:
        """Test successful user deletion."""
        # Arrange - create a user
        user_data = {
            "username": "deleteuser",
            "email": "delete@example.com",
            "first_name": "Delete",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        create_response = await admin_client.post("/v1/users/", json=user_data)
        assert create_response.status_code == 200

        user_id = create_response.json()["user_id"]

        # Act - delete the user
        response = await admin_client.delete(f"/v1/users/{user_id}/")

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert "message" in response_data
        assert response_data["message"] == "User deleted successfully"

        # Verify the deletion by trying to get the user again
        get_response = await admin_client.get(f"/v1/users/{user_id}/")

        # The user should not be found after deletion
        assert get_response.status_code == 404

        # Check error response structure
        error_data = get_response.json()
        assert "error" in error_data
        assert "message" in error_data
        # This is an HTTP exception, not a domain exception
        assert error_data["error"] == "HTTP Error"

    @pytest.mark.asyncio
    async def test_delete_user_not_found(
        self, admin_client: AsyncClient
    ) -> None:
        """Test deleting a non-existent user."""
        # Act - try to delete a non-existent user
        response = await admin_client.delete(
            "/v1/users/11111111-1111-1111-1111-111111111111/"
        )

        # Assert - should fail with 404 since user doesn't exist
        assert response.status_code == 404
        response_data = response.json()
        assert "error" in response_data
        assert response_data["error"] == "Resource Not Found"
        assert (
            "User 11111111-1111-1111-1111-111111111111 not found"
            in response_data["message"]
        )


class TestUserHistoricalQueries:
    """Test user historical queries with freezegun for time control."""

    @pytest.mark.asyncio
    async def test_user_history_unauthorized_no_jwt(
        self, unauthenticated_client: AsyncClient
    ) -> None:
        """Test that getting user history without JWT returns 401."""
        # Act
        response = await unauthenticated_client.get(
            "/v1/users/11111111-1111-1111-1111-111111111111/history/?timestamp=2025-01-01T10:00:00"
        )

        # Assert
        assert response.status_code == 401
        response_data = response.json()

        # Check error response structure
        assert "error" in response_data
        assert "message" in response_data
        assert response_data["error"] == "HTTP Error"
        assert "not authenticated" in response_data["message"].lower()

    @pytest.mark.asyncio
    async def test_user_history_success_regular_user(
        self, admin_client: AsyncClient, user_client: AsyncClient
    ) -> None:
        """Test that regular users can get user history (they have user:read permission)."""
        from freezegun import freeze_time

        # Arrange - create a user as admin first with controlled time
        with freeze_time("2025-08-16T12:00:00"):
            user_data = {
                "username": "historyreadableuser",
                "email": "historyreadable@example.com",
                "first_name": "History",
                "last_name": "Readable",
                "password": "password123",  # pragma: allowlist secret
            }

            create_response = await admin_client.post(
                "/v1/users/", json=user_data
            )
            assert create_response.status_code == 200

            user_id = create_response.json()["user_id"]

        # Act - get user history with regular user permissions at a time after creation
        with freeze_time("2025-08-16T12:01:00"):
            response = await user_client.get(
                f"/v1/users/{user_id}/history/?timestamp=2025-08-16T12:00:30"
            )

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure - user data is at the top level, not nested under "user"
        assert "id" in response_data
        assert "username" in response_data
        assert "email" in response_data
        assert "first_name" in response_data
        assert "last_name" in response_data
        assert "created_at" in response_data

        # Check user data values
        assert response_data["id"] == user_id
        assert response_data["username"] == "historyreadableuser"
        assert response_data["email"] == "historyreadable@example.com"
        assert response_data["first_name"] == "History"
        assert response_data["last_name"] == "Readable"

        # Check that created_at matches our frozen time
        assert response_data["created_at"] == "2025-08-16T12:00:00Z"

    @pytest.mark.asyncio
    async def test_user_history_success_regular_user_other_user(
        self, admin_client: AsyncClient, user_client: AsyncClient
    ) -> None:
        """Test that regular users can get user history for other users (they have user:read permission)."""
        from freezegun import freeze_time

        # Arrange - create a user as admin first with controlled time
        with freeze_time("2025-08-16T12:00:00"):
            user_data = {
                "username": "historyreadableuser",
                "email": "historyreadable@example.com",
                "first_name": "History",
                "last_name": "Readable",
                "password": "password123",  # pragma: allowlist secret
            }

            create_response = await admin_client.post(
                "/v1/users/", json=user_data
            )
            assert create_response.status_code == 200

            user_id = create_response.json()["user_id"]

        # Act - get user history with regular user permissions (should succeed with 200)
        with freeze_time("2025-08-16T12:01:00"):
            response = await user_client.get(
                f"/v1/users/{user_id}/history/?timestamp=2025-08-16T12:00:30"
            )

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure - user data is at the top level, not nested under "user"
        assert "id" in response_data
        assert "username" in response_data
        assert "email" in response_data
        assert "first_name" in response_data
        assert "last_name" in response_data
        assert "created_at" in response_data

        # Check user data values
        assert response_data["id"] == user_id
        assert response_data["username"] == "historyreadableuser"
        assert response_data["email"] == "historyreadable@example.com"
        assert response_data["first_name"] == "History"
        assert response_data["last_name"] == "Readable"

        # Check that created_at matches our frozen time
        assert response_data["created_at"] == "2025-08-16T12:00:00Z"

    @pytest.mark.asyncio
    async def test_user_history_at_different_timestamps(
        self, admin_client: AsyncClient, freezer: Any
    ) -> None:
        """Test user history at different timestamps using freezegun."""
        # Arrange - create a user at a specific time
        user_data = {
            "username": "historicaluser",
            "email": "historical@example.com",
            "first_name": "Historical",
            "last_name": "User",
            "password": "password123",  # pragma: allowlist secret
        }

        # Create user at 2025-01-01 10:00:00
        with freezer("2025-01-01 10:00:00"):
            create_response = await admin_client.post(
                "/v1/users/", json=user_data
            )
            assert create_response.status_code == 200
            user_id = create_response.json()["user_id"]

        # Update user at 2025-01-01 11:00:00
        with freezer("2025-01-01 11:00:00"):
            update_data = {
                "first_name": "Updated",
                "email": "updated@example.com",
            }
            update_response = await admin_client.put(
                f"/v1/users/{user_id}/", json=update_data
            )
            assert update_response.status_code == 200

        # Test 1: Get user state at creation time (should have original data)
        with freezer("2025-01-01 10:30:00"):
            response = await admin_client.get(
                f"/v1/users/{user_id}/history/?timestamp=2025-01-01T10:30:00"
            )
            assert response.status_code == 200

            user_state = response.json()
            assert user_state["first_name"] == "Historical"  # Original value
            assert (
                user_state["email"] == "historical@example.com"
            )  # Original value

        # Test 2: Get user state after update (should have updated data)
        with freezer("2025-01-01 11:30:00"):
            response = await admin_client.get(
                f"/v1/users/{user_id}/history/?timestamp=2025-01-01T11:30:00"
            )
            assert response.status_code == 200

            user_state = response.json()
            assert user_state["first_name"] == "Updated"  # Updated value
            assert (
                user_state["email"] == "updated@example.com"
            )  # Updated value

        # Test 3: Get user state before creation (should return 404)
        with freezer("2025-01-01 09:00:00"):
            response = await admin_client.get(
                f"/v1/users/{user_id}/history/?timestamp=2025-01-01T09:00:00"
            )
            assert response.status_code == 404

            error_data = response.json()
            assert "error" in error_data
            # This is an HTTP exception, not a domain exception
            assert error_data["error"] == "HTTP Error"
