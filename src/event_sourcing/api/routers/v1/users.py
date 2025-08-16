import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from event_sourcing.api.depends import InfrastructureFactoryDep
from event_sourcing.application.commands.user import (
    ChangePasswordCommand,
    CreateUserCommand,
    DeleteUserCommand,
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
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    GetUserResponse,
    ListUsersResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    UserDTO,
)
from event_sourcing.infrastructure.security.permissions import (
    CreateUserPermissionDep,
    DeleteUserPermissionDep,
    ReadUserPermissionDep,
    require_update_specific_user_permission_dep,
)

logger = logging.getLogger(__name__)

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post(
    "/", description="Create a new user", response_model=CreateUserResponse
)
async def create_user(
    user_data: CreateUserRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
    permission: CreateUserPermissionDep = None,
) -> CreateUserResponse:
    """Create a new user"""
    # Permission is checked automatically via dependency injection

    # Generate user ID
    user_id = uuid.uuid4()

    # Create command with plain password - will be hashed in command handler
    command = CreateUserCommand(
        user_id=user_id,
        username=user_data.username,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        password=user_data.password,
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
    infrastructure_factory: InfrastructureFactoryDep = None,
    permission: ReadUserPermissionDep = None,
) -> ListUsersResponse:
    """List users with pagination and filtering"""
    # Permission is checked automatically via dependency injection

    # Create query
    query = ListUsersQuery(
        page=page,
        page_size=page_size,
        username=username,
        email=email,
    )

    # Get query handler
    query_handler = infrastructure_factory.create_list_users_query_handler()

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


@users_router.put(
    "/{user_id}/",
    description="Update user information",
    response_model=UpdateUserResponse,
)
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
    permission: UserDTO = Depends(require_update_specific_user_permission_dep),
) -> UpdateUserResponse:
    """Update user information"""
    # Permission is checked automatically via dependency injection

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


@users_router.put(
    "/{user_id}/password/",
    description="Change user's password",
    response_model=ChangePasswordResponse,
)
async def change_password(
    user_id: str,
    password_data: ChangePasswordRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
    permission: UserDTO = Depends(require_update_specific_user_permission_dep),
) -> ChangePasswordResponse:
    """Change user's password"""
    # Permission is checked automatically via dependency injection

    # Create command with plain password - will be hashed in command handler
    command = ChangePasswordCommand(
        user_id=uuid.UUID(user_id),
        old_password=password_data.current_password,
        new_password=password_data.new_password,
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


@users_router.delete(
    "/{user_id}/", description="Delete user", response_model=DeleteUserResponse
)
async def delete_user(
    user_id: str,
    infrastructure_factory: InfrastructureFactoryDep = None,
    permission: DeleteUserPermissionDep = None,
) -> DeleteUserResponse:
    """Delete user"""
    # Permission is checked automatically via dependency injection

    # Create command
    command = DeleteUserCommand(user_id=uuid.UUID(user_id))

    # Get command handler
    command_handler = (
        infrastructure_factory.create_delete_user_command_handler()
    )

    # Process command
    await command_handler.handle(command)

    return DeleteUserResponse(message="User deleted successfully")


@users_router.get(
    "/{user_id}/", description="Get user by ID", response_model=GetUserResponse
)
async def get_user(
    user_id: str,
    infrastructure_factory: InfrastructureFactoryDep = None,
    permission: ReadUserPermissionDep = None,
) -> GetUserResponse:
    """Get user by ID"""
    # Permission is checked automatically via dependency injection

    # Create query
    query = GetUserQuery(user_id=uuid.UUID(user_id))

    # Get query handler
    query_handler = infrastructure_factory.create_get_user_query_handler()

    # Execute query
    user = await query_handler.handle(query)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return GetUserResponse(user=user)


@users_router.get(
    "/{user_id}/history/",
    description="Get user state at a specific point in time",
    response_model=UserDTO,
)
async def get_user_history(
    user_id: str,
    timestamp: str = Query(
        ..., description="Point in time (ISO format) - required"
    ),
    infrastructure_factory: InfrastructureFactoryDep = None,
    permission: ReadUserPermissionDep = None,
) -> UserDTO:
    """Get user state at a specific point in time"""
    # Permission is checked automatically via dependency injection

    # Parse the required timestamp
    timestamp_parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    # Create query
    query = GetUserHistoryQuery(
        user_id=uuid.UUID(user_id),
        timestamp=timestamp_parsed,
    )

    # Get query handler
    query_handler = (
        infrastructure_factory.create_get_user_history_query_handler()
    )

    # Execute query
    user = await query_handler.handle(query)

    if not user:
        raise HTTPException(
            status_code=404, detail="User not found at specified time"
        )

    return user
