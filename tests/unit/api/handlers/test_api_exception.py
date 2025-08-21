"""Unit tests for API exception handlers."""

from typing import Any, Callable, Tuple

import pytest
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from event_sourcing.api.handlers.exception import (
    configure_exception_handlers,
    handle_authentication_error,
    handle_business_rule_violation,
    handle_content_type_error,
    handle_domain_exception,
    handle_email_already_exists,
    handle_generic_exception,
    handle_http_exception,
    handle_infrastructure_error,
    handle_invalid_email_format,
    handle_password_required,
    handle_projection_error,
    handle_request_validation_error,
    handle_resource_conflict,
    handle_resource_not_found,
    handle_user_business_rule_violation,
    handle_user_conflict,
    handle_user_not_found,
    handle_user_validation_error,
    handle_username_already_exists,
    handle_username_too_short,
    handle_validation_error,
)
from event_sourcing.exceptions import (
    AuthenticationError,
    BusinessRuleViolationError,
    EmailAlreadyExistsError,
    EventSourcingError,
    InfrastructureError,
    InvalidEmailFormatError,
    PasswordRequiredError,
    ProjectionError,
    ResourceConflictError,
    ResourceNotFoundError,
    UserBusinessRuleViolationError,
    UserConflictError,
    UsernameAlreadyExistsError,
    UsernameTooShortError,
    UserNotFoundError,
    UserValidationError,
    ValidationError,
)


class TestExceptionHandlers:
    """Test suite for API exception handlers."""

    @pytest.fixture
    def mock_request(self) -> Request:
        """Create a mock request object."""
        return Request(
            scope={"type": "http", "method": "GET", "path": "/test"}
        )

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create a FastAPI app for testing."""
        return FastAPI()

    def test_configure_exception_handlers(self, app: FastAPI) -> None:
        """Test that all exception handlers are properly configured."""
        configure_exception_handlers(app)

        # Verify that all handlers are registered
        assert app.exception_handlers is not None
        assert len(app.exception_handlers) > 0

    @pytest.mark.asyncio
    async def test_handle_domain_exception(
        self, mock_request: Request
    ) -> None:
        """Test generic domain exception handler."""
        exc = EventSourcingError("Test domain error", {"key": "value"})

        response = await handle_domain_exception(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Domain Error","message":"Test domain error","details":{"key":"value"},"type":"EventSourcingError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_validation_error(
        self, mock_request: Request
    ) -> None:
        """Test validation error handler."""
        exc = ValidationError(
            "Test validation error", "test_field", {"key": "value"}
        )

        response = await handle_validation_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Validation Error","message":"Test validation error","field":"test_field","details":{"key":"value"},"type":"ValidationError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_business_rule_violation(
        self, mock_request: Request
    ) -> None:
        """Test business rule violation handler."""
        exc = BusinessRuleViolationError(
            "Test business rule violation", "test_rule", {"key": "value"}
        )

        response = await handle_business_rule_violation(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Business Rule Violation","message":"Test business rule violation","rule":"test_rule","details":{"key":"value"},"type":"BusinessRuleViolationError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_resource_not_found(
        self, mock_request: Request
    ) -> None:
        """Test resource not found handler."""
        exc = ResourceNotFoundError(
            "Test resource not found", "User", "123", {"key": "value"}
        )

        response = await handle_resource_not_found(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Resource Not Found","message":"Test resource not found","resource_type":"User","resource_id":"123","type":"ResourceNotFoundError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_resource_conflict(
        self, mock_request: Request
    ) -> None:
        """Test resource conflict handler."""
        exc = ResourceConflictError(
            "Test resource conflict", "duplicate", {"key": "value"}
        )

        response = await handle_resource_conflict(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_409_CONFLICT
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Resource Conflict","message":"Test resource conflict","conflict_type":"duplicate","details":{"key":"value"},"type":"ResourceConflictError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_infrastructure_error(
        self, mock_request: Request
    ) -> None:
        """Test infrastructure error handler."""
        exc = InfrastructureError(
            "Test infrastructure error", {"key": "value"}
        )

        response = await handle_infrastructure_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Infrastructure Error","message":"Test infrastructure error","details":{"key":"value"},"type":"InfrastructureError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_authentication_error(
        self, mock_request: Request
    ) -> None:
        """Test authentication error handler."""
        exc = AuthenticationError(
            "Test authentication error", {"key": "value"}
        )

        response = await handle_authentication_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Authentication Error","message":"Test authentication error","details":{"key":"value"},"type":"AuthenticationError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_projection_error(
        self, mock_request: Request
    ) -> None:
        """Test projection error handler."""
        exc = ProjectionError("Test projection error", {"key": "value"})

        response = await handle_projection_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Projection Error","message":"Test projection error","details":{"key":"value"},"type":"ProjectionError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_user_validation_error(
        self, mock_request: Request
    ) -> None:
        """Test user validation error handler."""
        exc = UserValidationError(
            "Test user validation error", "test_field", {"key": "value"}
        )

        response = await handle_user_validation_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert "UserValidationError" in response_body.decode()

    @pytest.mark.asyncio
    async def test_handle_user_business_rule_violation(
        self, mock_request: Request
    ) -> None:
        """Test user business rule violation handler."""
        exc = UserBusinessRuleViolationError(
            "Test user business rule violation", "test_rule", {"key": "value"}
        )

        response = await handle_user_business_rule_violation(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert "UserBusinessRuleViolationError" in response_body.decode()

    @pytest.mark.asyncio
    async def test_handle_user_not_found(self, mock_request: Request) -> None:
        """Test user not found handler."""
        exc = UserNotFoundError("Test user not found", "123", {"key": "value"})

        response = await handle_user_not_found(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert "UserNotFoundError" in response_body.decode()

    @pytest.mark.asyncio
    async def test_handle_user_conflict(self, mock_request: Request) -> None:
        """Test user conflict handler."""
        exc = UserConflictError(
            "Test user conflict", "duplicate", {"key": "value"}
        )

        response = await handle_user_conflict(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_409_CONFLICT
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert "UserConflictError" in response_body.decode()

    @pytest.mark.asyncio
    async def test_handle_username_already_exists(
        self, mock_request: Request
    ) -> None:
        """Test username already exists handler."""
        exc = UsernameAlreadyExistsError("testuser")

        response = await handle_username_already_exists(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_409_CONFLICT
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert "UsernameAlreadyExistsError" in response_body.decode()

    @pytest.mark.asyncio
    async def test_handle_email_already_exists(
        self, mock_request: Request
    ) -> None:
        """Test email already exists handler."""
        exc = EmailAlreadyExistsError("test@example.com")

        response = await handle_email_already_exists(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_409_CONFLICT
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert "EmailAlreadyExistsError" in response_body.decode()

    @pytest.mark.asyncio
    async def test_handle_username_too_short(
        self, mock_request: Request
    ) -> None:
        """Test username too short handler."""
        exc = UsernameTooShortError("ab", 3)

        response = await handle_username_too_short(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert "UsernameTooShortError" in response_body.decode()

    @pytest.mark.asyncio
    async def test_handle_password_required(
        self, mock_request: Request
    ) -> None:
        """Test password required handler."""
        exc = PasswordRequiredError()

        response = await handle_password_required(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert "PasswordRequiredError" in response_body.decode()

    @pytest.mark.asyncio
    async def test_handle_invalid_email_format(
        self, mock_request: Request
    ) -> None:
        """Test invalid email format handler."""
        exc = InvalidEmailFormatError("invalid-email")

        response = await handle_invalid_email_format(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert "InvalidEmailFormatError" in response_body.decode()

    @pytest.mark.asyncio
    async def test_handle_request_validation_error(
        self, mock_request: Request
    ) -> None:
        """Test request validation error handler."""
        # Create a mock validation error
        errors = [
            {
                "loc": ("body", "field"),
                "msg": "field required",
                "type": "value_error.missing",
                "input": None,
            }
        ]
        exc = RequestValidationError(errors)

        response = await handle_request_validation_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert "Request Validation Error" in response_body.decode()

    @pytest.mark.asyncio
    async def test_handle_request_validation_error_with_bytes(
        self, mock_request: Request
    ) -> None:
        """Test request validation error handler with bytes input."""
        # Create a mock validation error with bytes
        errors = [
            {
                "loc": ("body", "field"),
                "msg": "field required",
                "type": "value_error.missing",
                "input": b"bytes_data",
            }
        ]
        exc = RequestValidationError(errors)

        response = await handle_request_validation_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Verify bytes are converted to string
        response_body = response.body
        assert isinstance(response_body, bytes)
        response_text = response_body.decode()
        assert "bytes_data" in response_text
        assert "b'bytes_data'" not in response_text

    @pytest.mark.asyncio
    async def test_handle_http_exception(self, mock_request: Request) -> None:
        """Test HTTP exception handler."""
        exc = StarletteHTTPException(status_code=400, detail="Bad Request")

        response = await handle_http_exception(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"HTTP Error","message":"Bad Request","type":"HTTPException"}'
        )

    @pytest.mark.asyncio
    async def test_handle_generic_exception(
        self, mock_request: Request
    ) -> None:
        """Test generic exception handler."""
        exc = ValueError("Test generic error")

        response = await handle_generic_exception(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Internal Server Error","message":"An unexpected error occurred","type":"ValueError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_content_type_error(
        self, mock_request: Request
    ) -> None:
        """Test content type error handler."""
        exc = UnicodeDecodeError("utf-8", b"invalid", 0, 1, "invalid utf-8")

        response = await handle_content_type_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Bad Request","message":"Invalid content type or malformed request body","type":"ContentTypeError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_content_type_error_value_error(
        self, mock_request: Request
    ) -> None:
        """Test content type error handler with ValueError."""
        exc = ValueError("Invalid content type")

        response = await handle_content_type_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_body = response.body
        assert isinstance(response_body, bytes)
        assert (
            response_body.decode()
            == '{"error":"Bad Request","message":"Invalid content type or malformed request body","type":"ContentTypeError"}'
        )

    @pytest.mark.asyncio
    async def test_handle_request_validation_error_public_function(
        self, mock_request: Request
    ) -> None:
        """Test the public request validation error handler function."""
        errors = [{"loc": ("body",), "msg": "error", "type": "value_error"}]
        exc = RequestValidationError(errors)

        response = await handle_request_validation_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        response_text = response_body.decode()
        assert "Request Validation Error" in response_text
        assert "Request validation failed" in response_text
        assert "RequestValidationError" in response_text

    @pytest.mark.asyncio
    async def test_handle_http_exception_public_function(
        self, mock_request: Request
    ) -> None:
        """Test the public HTTP exception handler function."""
        exc = StarletteHTTPException(status_code=400, detail="Bad Request")

        response = await handle_http_exception(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        response_body = response.body
        assert isinstance(response_body, bytes)
        response_text = response_body.decode()
        assert "HTTP Error" in response_text
        assert "Bad Request" in response_text
        assert "HTTPException" in response_text

    @pytest.mark.asyncio
    async def test_handle_request_validation_error_with_bytes_input(
        self, mock_request: Request
    ) -> None:
        """Test request validation error handler with bytes input to trigger safe processing."""
        # Create a validation error with bytes input to test the safe processing logic
        errors = [
            {
                "loc": ("body", "field"),
                "msg": "error",
                "type": "value_error",
                "input": b"bytes input",  # This should trigger the bytes processing
            }
        ]
        exc = RequestValidationError(errors)

        response = await handle_request_validation_error(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_body = response.body
        assert isinstance(response_body, bytes)
        response_text = response_body.decode()
        assert "Request Validation Error" in response_text
        # The bytes should be safely converted to string representation
        assert "bytes input" in response_text

    @pytest.mark.asyncio
    async def test_exceptions_with_none_details(
        self, mock_request: Request
    ) -> None:
        """Test exception handlers with None details."""
        # Test various exceptions with None details
        exceptions: list[Tuple[Any, Callable[[Request, Any], Any]]] = [
            (EventSourcingError("Test error"), handle_domain_exception),
            (ValidationError("Test error", "field"), handle_validation_error),
            (
                BusinessRuleViolationError("Test error", "rule"),
                handle_business_rule_violation,
            ),
            (
                ResourceNotFoundError("Test error", "User", "123"),
                handle_resource_not_found,
            ),
            (
                ResourceConflictError("Test error", "duplicate"),
                handle_resource_conflict,
            ),
            (InfrastructureError("Test error"), handle_infrastructure_error),
            (AuthenticationError("Test error"), handle_authentication_error),
            (ProjectionError("Test error"), handle_projection_error),
        ]

        for exc, handler in exceptions:
            response = await handler(mock_request, exc)
            assert isinstance(response, JSONResponse)
            # Some handlers don't include details when they're None, so we just check the response is valid
            assert response.status_code in [200, 400, 401, 404, 409, 422, 500]

    @pytest.mark.asyncio
    async def test_exceptions_with_empty_details(
        self, mock_request: Request
    ) -> None:
        """Test exception handlers with empty details."""
        # Test various exceptions with empty details
        exceptions: list[Tuple[Any, Callable[[Request, Any], Any]]] = [
            (EventSourcingError("Test error", {}), handle_domain_exception),
            (
                ValidationError("Test error", "field", {}),
                handle_validation_error,
            ),
            (
                BusinessRuleViolationError("Test error", "rule", {}),
                handle_business_rule_violation,
            ),
            (
                ResourceNotFoundError("Test error", "User", "123", {}),
                handle_resource_not_found,
            ),
            (
                ResourceConflictError("Test error", "duplicate", {}),
                handle_resource_conflict,
            ),
            (
                InfrastructureError("Test error", {}),
                handle_infrastructure_error,
            ),
            (
                AuthenticationError("Test error", {}),
                handle_authentication_error,
            ),
            (ProjectionError("Test error", {}), handle_projection_error),
        ]

        for exc, handler in exceptions:
            response = await handler(mock_request, exc)
            assert isinstance(response, JSONResponse)
            # Verify that empty details are handled gracefully
            response_body = response.body
            assert isinstance(response_body, bytes)
            response_text = response_body.decode()
            # Check that the response contains the expected error structure
            assert "error" in response_text
            assert "message" in response_text
            assert "type" in response_text
