import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr

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
)

logger = logging.getLogger(__name__)

users_router = APIRouter(prefix="/users", tags=["users"])


# Request/Response models
class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str  # Will be hashed before storing


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class ChangeUsernameRequest(BaseModel):
    new_username: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class CompletePasswordResetRequest(BaseModel):
    new_password: str
    reset_token: str


@users_router.post("/", description="Create a new user")
async def create_user(
    user_data: CreateUserRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
    """Create a new user"""
    try:
        # Generate user ID
        user_id = uuid.uuid4()

        # In a real app, you would hash the password here
        password_hash = f"hashed_{user_data.password}"  # Placeholder

        # Create command
        command = CreateUserCommand(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password_hash=password_hash,
        )

        # Get command handler
        command_handler = (
            infrastructure_factory.create_create_user_command_handler()
        )

        # Process command
        await command_handler.handle(command)

        return {
            "status": "success",
            "message": "User created successfully",
            "user_id": str(user_id),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.put("/{user_id}", description="Update user information")
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
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

        return {"status": "success", "message": "User updated successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.put("/{user_id}/username", description="Change user's username")
async def change_username(
    user_id: str,
    username_data: ChangeUsernameRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
    """Change user's username"""
    try:
        # Create command
        command = ChangeUsernameCommand(
            user_id=uuid.UUID(user_id), new_username=username_data.new_username
        )

        # Get command handler
        command_handler = (
            infrastructure_factory.create_change_username_command_handler()
        )

        # Process command
        await command_handler.handle(command)

        return {
            "status": "success",
            "message": "Username changed successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error changing username: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.put("/{user_id}/password", description="Change user's password")
async def change_password(
    user_id: str,
    password_data: ChangePasswordRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
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

        return {
            "status": "success",
            "message": "Password changed successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.post(
    "/password-reset/request", description="Request password reset"
)
async def request_password_reset(
    reset_data: RequestPasswordResetRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
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

        return {"status": "success", "message": "Password reset email sent"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error requesting password reset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.post(
    "/password-reset/complete", description="Complete password reset"
)
async def complete_password_reset(
    reset_data: CompletePasswordResetRequest,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
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

        return {
            "status": "success",
            "message": "Password reset completed successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing password reset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.delete("/{user_id}", description="Delete user")
async def delete_user(
    user_id: str,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
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

        return {"status": "success", "message": "User deleted successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.get("/{user_id}", description="Get user by ID")
async def get_user(
    user_id: str,
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
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

        return {"status": "success", "user": user}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@users_router.get("/{user_id}/history", description="Get user event history")
async def get_user_history(
    user_id: str,
    from_date: Optional[str] = Query(
        None, description="Start date (ISO format)"
    ),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    infrastructure_factory: InfrastructureFactoryDep = None,
) -> Dict[str, Any]:
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

        return {
            "status": "success",
            "user_id": user_id,
            "count": len(events),
            "events": events,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
