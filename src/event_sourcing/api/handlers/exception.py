"""Exception handlers for mapping domain exceptions to HTTP responses."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

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

logger = logging.getLogger(__name__)


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers for the FastAPI application."""

    # Domain exception handlers
    app.add_exception_handler(EventSourcingError, handle_domain_exception)
    app.add_exception_handler(ValidationError, handle_validation_error)
    app.add_exception_handler(
        BusinessRuleViolationError, handle_business_rule_violation
    )
    app.add_exception_handler(ResourceNotFoundError, handle_resource_not_found)
    app.add_exception_handler(ResourceConflictError, handle_resource_conflict)

    # New exception category handlers
    app.add_exception_handler(InfrastructureError, handle_infrastructure_error)
    app.add_exception_handler(AuthenticationError, handle_authentication_error)
    app.add_exception_handler(ProjectionError, handle_projection_error)

    # User-specific exception handlers
    app.add_exception_handler(
        UserValidationError, handle_user_validation_error
    )
    app.add_exception_handler(
        UserBusinessRuleViolationError, handle_user_business_rule_violation
    )
    app.add_exception_handler(UserNotFoundError, handle_user_not_found)
    app.add_exception_handler(UserConflictError, handle_user_conflict)
    app.add_exception_handler(
        UsernameAlreadyExistsError, handle_username_already_exists
    )
    app.add_exception_handler(
        EmailAlreadyExistsError, handle_email_already_exists
    )
    app.add_exception_handler(UsernameTooShortError, handle_username_too_short)
    app.add_exception_handler(PasswordRequiredError, handle_password_required)
    app.add_exception_handler(
        InvalidEmailFormatError, handle_invalid_email_format
    )

    # FastAPI built-in exception handlers
    app.add_exception_handler(
        RequestValidationError,
        _handle_request_validation_error_wrapper,
    )
    app.add_exception_handler(
        StarletteHTTPException,
        _handle_http_exception_wrapper,
    )

    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, handle_generic_exception)

    # Content type error handler
    app.add_exception_handler(UnicodeDecodeError, handle_content_type_error)
    app.add_exception_handler(ValueError, handle_content_type_error)


async def handle_domain_exception(
    request: Request, exc: EventSourcingError
) -> JSONResponse:
    """Handle generic domain exceptions."""
    logger.warning(
        f"Domain exception: {exc.message}", extra={"details": exc.details}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Domain Error",
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


async def handle_validation_error(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(
        f"Validation error: {exc.message}",
        extra={"field": exc.field, "details": exc.details},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": exc.message,
            "field": exc.field,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


async def handle_business_rule_violation(
    request: Request, exc: BusinessRuleViolationError
) -> JSONResponse:
    """Handle business rule violations."""
    logger.warning(
        f"Business rule violation: {exc.message}",
        extra={"rule": exc.rule_name, "details": exc.details},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Business Rule Violation",
            "message": exc.message,
            "rule": exc.rule_name,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


async def handle_resource_not_found(
    request: Request, exc: ResourceNotFoundError
) -> JSONResponse:
    """Handle resource not found errors."""
    logger.debug(
        f"Resource not found: {exc.message}",
        extra={
            "resource_type": exc.resource_type,
            "resource_id": exc.resource_id,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Resource Not Found",
            "message": exc.message,
            "resource_type": exc.resource_type,
            "resource_id": exc.resource_id,
            "type": exc.__class__.__name__,
        },
    )


async def handle_resource_conflict(
    request: Request, exc: ResourceConflictError
) -> JSONResponse:
    """Handle resource conflicts."""
    logger.warning(
        f"Resource conflict: {exc.message}",
        extra={"conflict_type": exc.conflict_type, "details": exc.details},
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Resource Conflict",
            "message": exc.message,
            "conflict_type": exc.conflict_type,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


async def handle_infrastructure_error(
    request: Request, exc: InfrastructureError
) -> JSONResponse:
    """Handle infrastructure errors."""
    logger.error(
        f"Infrastructure error: {exc.message}", extra={"details": exc.details}
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Infrastructure Error",
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


async def handle_authentication_error(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    """Handle authentication errors."""
    logger.warning(
        f"Authentication error: {exc.message}", extra={"details": exc.details}
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "Authentication Error",
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


async def handle_projection_error(
    request: Request, exc: ProjectionError
) -> JSONResponse:
    """Handle projection errors."""
    logger.error(
        f"Projection error: {exc.message}", extra={"details": exc.details}
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Projection Error",
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


# User-specific handlers
async def handle_user_validation_error(
    request: Request, exc: UserValidationError
) -> JSONResponse:
    """Handle user validation errors."""
    return await handle_validation_error(request, exc)


async def handle_user_business_rule_violation(
    request: Request, exc: UserBusinessRuleViolationError
) -> JSONResponse:
    """Handle user business rule violations."""
    return await handle_business_rule_violation(request, exc)


async def handle_user_not_found(
    request: Request, exc: UserNotFoundError
) -> JSONResponse:
    """Handle user not found errors."""
    return await handle_resource_not_found(request, exc)


async def handle_user_conflict(
    request: Request, exc: UserConflictError
) -> JSONResponse:
    """Handle user conflicts."""
    return await handle_resource_conflict(request, exc)


async def handle_username_already_exists(
    request: Request, exc: UsernameAlreadyExistsError
) -> JSONResponse:
    """Handle username already exists errors."""
    return await handle_user_conflict(request, exc)


async def handle_email_already_exists(
    request: Request, exc: EmailAlreadyExistsError
) -> JSONResponse:
    """Handle email already exists errors."""
    return await handle_user_conflict(request, exc)


async def handle_username_too_short(
    request: Request, exc: UsernameTooShortError
) -> JSONResponse:
    """Handle username too short errors."""
    return await handle_user_validation_error(request, exc)


async def handle_password_required(
    request: Request, exc: PasswordRequiredError
) -> JSONResponse:
    """Handle password required errors."""
    return await handle_user_validation_error(request, exc)


async def handle_invalid_email_format(
    request: Request, exc: InvalidEmailFormatError
) -> JSONResponse:
    """Handle invalid email format errors."""
    return await handle_user_validation_error(request, exc)


# FastAPI built-in exception handlers
async def handle_request_validation_error(
    request: Request, exc: RequestValidationError
) -> Response:
    """Handle request validation errors."""
    logger.warning(f"Request validation error: {exc.errors()}")

    # Safely process errors to handle non-serializable content like bytes
    safe_errors = []
    for error in exc.errors():
        safe_error = error.copy()
        # Convert bytes to string representation if present
        if isinstance(safe_error.get("input"), bytes):
            safe_error["input"] = safe_error["input"].decode(
                "utf-8", errors="replace"
            )
        safe_errors.append(safe_error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Request Validation Error",
            "message": "Request validation failed",
            "details": safe_errors,
            "type": "RequestValidationError",
        },
    )


async def handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> Response:
    """Handle HTTP exceptions."""
    logger.debug(f"HTTP exception: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "type": "HTTPException",
        },
    )


async def handle_generic_exception(
    request: Request, exc: Exception
) -> Response:
    """Handle generic exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "type": exc.__class__.__name__,
        },
    )


async def handle_content_type_error(
    request: Request, exc: Exception
) -> Response:
    """Handle content type errors gracefully.

    This handler prevents crashes when invalid content types are sent
    in request bodies, such as bytes or malformed content.
    """
    logger.warning(f"Content type error: {exc}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "message": "Invalid content type or malformed request body",
            "type": "ContentTypeError",
        },
    )


# Wrapper functions to satisfy Starlette's type requirements
async def _handle_request_validation_error_wrapper(
    request: Request, exc: Exception
) -> Response:
    """Wrapper for RequestValidationError handler."""
    if isinstance(exc, RequestValidationError):
        return await handle_request_validation_error(request, exc)
    raise TypeError(f"Expected RequestValidationError, got {type(exc)}")


async def _handle_http_exception_wrapper(
    request: Request, exc: Exception
) -> Response:
    """Wrapper for HTTPException handler."""
    if isinstance(exc, StarletteHTTPException):
        return await handle_http_exception(request, exc)
    raise TypeError(f"Expected StarletteHTTPException, got {type(exc)}")
