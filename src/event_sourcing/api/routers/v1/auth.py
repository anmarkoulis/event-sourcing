"""Authentication router for login."""

import logging

from fastapi import APIRouter, HTTPException, status

from event_sourcing.dto.auth import LoginRequest, LoginResponse
from event_sourcing.infrastructure.security.provider import AuthServiceDep

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["authentication"])


@auth_router.post("/login/", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthServiceDep,
) -> LoginResponse:
    """Authenticate user and return JWT token.

    :param login_data: Login credentials.
    :param auth_service: Authentication service.
    :return: JWT token and user information.
    :raises HTTPException: If authentication fails.
    """
    user = await auth_service.authenticate_user(
        login_data.username, login_data.password
    )
    logger.info(f"User: {user}")

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(
        data={"sub": user.username, "user_id": str(user.id), "role": user.role}
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",  # noqa: S106
        user=user,
    )
