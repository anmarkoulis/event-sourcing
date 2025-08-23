"""Permission dependencies for API endpoints using JWT scopes."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from event_sourcing.dto.user import UserDTO
from event_sourcing.enums import Permission

from .provider import get_auth_service
from .services import AuthServiceInterface

# JWT security scheme - set auto_error=False to handle missing tokens manually
security = HTTPBearer(auto_error=False)


async def get_current_user_with_scope(
    required_scope: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthServiceInterface = Depends(get_auth_service),
) -> UserDTO:
    """Get current authenticated user and verify they have the required scope.

    :param required_scope: The scope required for access.
    :param credentials: HTTP authorization credentials.
    :param auth_service: Authentication service.
    :return: Current authenticated user.
    :raises HTTPException: If user lacks required scope or is not authenticated.
    """
    # Check if credentials are provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get current user
    current_user = await auth_service.get_current_user(credentials)

    # Decode JWT to get scopes
    token = credentials.credentials
    payload = auth_service.verify_token(token)

    scopes = payload.get("scopes", [])
    if required_scope not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required scope: {required_scope}",
        )

    return current_user


# Simple permission dependencies
async def require_create_user_permission(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthServiceInterface = Depends(get_auth_service),
) -> UserDTO:
    return await get_current_user_with_scope(
        Permission.USER_CREATE, credentials, auth_service
    )


async def require_read_user_permission(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthServiceInterface = Depends(get_auth_service),
) -> UserDTO:
    return await get_current_user_with_scope(
        Permission.USER_READ, credentials, auth_service
    )


async def require_update_specific_user_permission(
    user_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthServiceInterface = Depends(get_auth_service),
) -> UserDTO:
    """Check if user can update a specific user (own data or admin)."""
    # Check if credentials are provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get current user
    current_user = await auth_service.get_current_user(credentials)

    # Decode JWT to get scopes
    token = credentials.credentials
    payload = auth_service.verify_token(token)

    scopes = payload.get("scopes", [])

    # Admin can update any user
    if Permission.USER_DELETE in scopes:  # USER_DELETE indicates admin role
        return current_user

    # Regular users can only update their own data
    if str(current_user.id) == user_id:
        return current_user

    # Regular users cannot update other users' data
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions. You can only update your own user data.",
    )


async def require_update_specific_user_permission_dep(
    user_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthServiceInterface = Depends(get_auth_service),
) -> UserDTO:
    """Dependency that checks if user can update a specific user (own data or admin)."""
    return await require_update_specific_user_permission(
        user_id, credentials, auth_service
    )


async def require_delete_user_permission(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthServiceInterface = Depends(get_auth_service),
) -> UserDTO:
    return await get_current_user_with_scope(
        Permission.USER_DELETE, credentials, auth_service
    )


# Type aliases for FastAPI dependency injection
CreateUserPermissionDep = Annotated[
    UserDTO, Depends(require_create_user_permission)
]
ReadUserPermissionDep = Annotated[
    UserDTO, Depends(require_read_user_permission)
]
UpdateSpecificUserPermissionDep = Annotated[
    UserDTO, Depends(require_update_specific_user_permission)
]
DeleteUserPermissionDep = Annotated[
    UserDTO, Depends(require_delete_user_permission)
]
