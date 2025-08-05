import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from event_sourcing.api.depends import InfrastructureFactoryDep
from event_sourcing.application.commands.user import (
    ChangePasswordCommand,
    ChangeUsernameCommand,
    CompletePasswordResetCommand,
    CreateUserCommand,
    DeleteUserCommand,
    RequestPasswordResetCommand,
    UpdateUserCommand,
)
from event_sourcing.application.queries.user import (
    GetUserHistoryQuery,
    GetUserQuery,
    ListUsersQuery,
)
from event_sourcing.dto.user import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    ChangeUsernameRequest,
    ChangeUsernameResponse,
    CompletePasswordResetRequest,
    CompletePasswordResetResponse,
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    GetUserHistoryResponse,
    GetUserResponse,
    ListUsersResponse,
    RequestPasswordResetRequest,
    RequestPasswordResetResponse,
    UpdateUserRequest,
    UpdateUserResponse,
)

logger = logging.getLogger(__name__)

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post(
    "/", description="Create a new user", response_model=CreateUserResponse
)
async def create_user(
    user_data: CreateUserRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> CreateUserResponse:
    """Create a new user"""
    try:
        # Generate user ID
        user_id = uuid.uuid4()

        # Hash password (in real app, use proper hashing)
        password_hash = f"hashed_{user_data.password}"

        # Create command
        command = CreateUserCommand(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password_hash=password_hash,
        )

        # Get fully built command handler from factory
        command_handler = (
            infrastructure_factory.create_create_user_command_handler()
        )

        # Process command
        await command_handler.handle(command)

        return CreateUserResponse(
            message="User created successfully",
            user_id=str(user_id),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.get(
    "/",
    description="List users with pagination and filtering",
    response_model=ListUsersResponse,
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Number of items per page"
    ),
    username: Optional[str] = Query(
        None, description="Filter by username (partial match)"
    ),
    email: Optional[str] = Query(
        None, description="Filter by email (partial match)"
    ),
    status: Optional[str] = Query(None, description="Filter by status"),
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> ListUsersResponse:
    """List users with pagination and filtering"""
    try:
        # Create query
        query = ListUsersQuery(
            page=page,
            page_size=page_size,
            username=username,
            email=email,
            status=status,
        )

        # Get query handler
        query_handler = (
            infrastructure_factory.create_list_users_query_handler()
        )

        # Execute query
        result = await query_handler.handle(query)

        return ListUsersResponse(
            results=result["results"],
            next=result["next"],
            previous=result["previous"],
            count=result["count"],
            page=result["page"],
            page_size=result["page_size"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.put(
    "/{user_id}/",
    description="Update user information",
    response_model=UpdateUserResponse,
)
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> UpdateUserResponse:
    """Update user information"""
    try:
        # Create command
        command = UpdateUserCommand(
            user_id=uuid.UUID(user_id),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
        )

        # Get command handler
        command_handler = (
            infrastructure_factory.create_update_user_command_handler()
        )

        # Process command
        await command_handler.handle(command)

        return UpdateUserResponse(message="User updated successfully")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.put(
    "/{user_id}/username/",
    description="Change user's username",
    response_model=ChangeUsernameResponse,
)
async def change_username(
    user_id: str,
    username_data: ChangeUsernameRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> ChangeUsernameResponse:
    """Change user's username"""
    try:
        logger.info(f"API: Starting username change for user: {user_id}")

        # Create command
        command = ChangeUsernameCommand(
            user_id=uuid.UUID(user_id), new_username=username_data.new_username
        )
        logger.info(f"API: Created command for user: {user_id}")

        # Get command handler
        command_handler = (
            infrastructure_factory.create_change_username_command_handler()
        )
        logger.info(f"API: Got command handler for user: {user_id}")

        # Process command
        logger.info(f"API: Calling command handler for user: {user_id}")
        await command_handler.handle(command)
        logger.info(f"API: Command handler completed for user: {user_id}")

        return ChangeUsernameResponse(
            message="Username changed successfully",
        )

    except ValueError as e:
        logger.error(f"API: ValueError in change_username: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"API: Error changing username: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.put(
    "/{user_id}/password/",
    description="Change user's password",
    response_model=ChangePasswordResponse,
)
async def change_password(
    user_id: str,
    password_data: ChangePasswordRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> ChangePasswordResponse:
    """Change user's password"""
    try:
        # In a real app, you would verify current password and hash new password
        new_password_hash = (
            f"hashed_{password_data.new_password}"  # Placeholder
        )

        # Create command
        command = ChangePasswordCommand(
            user_id=uuid.UUID(user_id), new_password_hash=new_password_hash
        )

        # Get command handler
        command_handler = (
            infrastructure_factory.create_change_password_command_handler()
        )

        # Process command
        await command_handler.handle(command)

        return ChangePasswordResponse(
            message="Password changed successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.post(
    "/password-reset/request/",
    description="Request password reset",
    response_model=RequestPasswordResetResponse,
)
async def request_password_reset(
    reset_data: RequestPasswordResetRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> RequestPasswordResetResponse:
    """Request password reset"""
    try:
        # In a real app, you would find user by email first
        # For now, we'll assume we have the user_id
        user_id = uuid.uuid4()  # Placeholder - should find by email

        # Create command
        command = RequestPasswordResetCommand(user_id=user_id)

        # Get command handler
        command_handler = infrastructure_factory.create_request_password_reset_command_handler()

        # Process command
        await command_handler.handle(command)

        return RequestPasswordResetResponse(
            message="Password reset email sent"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error requesting password reset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.post(
    "/password-reset/complete/",
    description="Complete password reset",
    response_model=CompletePasswordResetResponse,
)
async def complete_password_reset(
    reset_data: CompletePasswordResetRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> CompletePasswordResetResponse:
    """Complete password reset"""
    try:
        # In a real app, you would validate the reset token and find user
        user_id = uuid.uuid4()  # Placeholder - should find by token

        # Hash the new password
        new_password_hash = f"hashed_{reset_data.new_password}"  # Placeholder

        # Create command
        command = CompletePasswordResetCommand(
            user_id=user_id,
            new_password_hash=new_password_hash,
            reset_token=reset_data.reset_token,
        )

        # Get command handler
        command_handler = infrastructure_factory.create_complete_password_reset_command_handler()

        # Process command
        await command_handler.handle(command)

        return CompletePasswordResetResponse(
            message="Password reset completed successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing password reset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.delete(
    "/{user_id}/", description="Delete user", response_model=DeleteUserResponse
)
async def delete_user(
    user_id: str,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> DeleteUserResponse:
    """Delete user"""
    try:
        # Create command
        command = DeleteUserCommand(user_id=uuid.UUID(user_id))

        # Get command handler
        command_handler = (
            infrastructure_factory.create_delete_user_command_handler()
        )

        # Process command
        await command_handler.handle(command)

        return DeleteUserResponse(message="User deleted successfully")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.get(
    "/{user_id}/", description="Get user by ID", response_model=GetUserResponse
)
async def get_user(
    user_id: str,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> GetUserResponse:
    """Get user by ID"""
    try:
        # Create query
        query = GetUserQuery(user_id=uuid.UUID(user_id))

        # Get query handler
        query_handler = infrastructure_factory.create_get_user_query_handler()

        # Execute query
        user = await query_handler.handle(query)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return GetUserResponse(user=user)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.get(
    "/{user_id}/history/",
    description="Get user event history",
    response_model=GetUserHistoryResponse,
)
async def get_user_history(
    user_id: str,
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> GetUserHistoryResponse:
    """Get event history for a specific user"""
    try:
        # Parse dates if provided
        from_date_parsed = None
        to_date_parsed = None

        if from_date:
            from_date_parsed = datetime.fromisoformat(
                from_date.replace("Z", "+00:00")
            )

        if to_date:
            to_date_parsed = datetime.fromisoformat(
                to_date.replace("Z", "+00:00")
            )

        # Create query
        query = GetUserHistoryQuery(
            user_id=uuid.UUID(user_id),
            from_date=from_date_parsed,
            to_date=to_date_parsed,
        )

        # Get query handler
        query_handler = (
            infrastructure_factory.create_get_user_history_query_handler()
        )

        # Execute query
        events = await query_handler.handle(query)

        return GetUserHistoryResponse(
            user_id=user_id,
            count=len(events),
            events=events,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
