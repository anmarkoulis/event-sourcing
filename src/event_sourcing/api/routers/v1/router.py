"""V1 API router that includes all v1 endpoints."""

from fastapi import APIRouter

from event_sourcing.api.routers.v1.users import users_router

# Create v1 router with the v1 prefix
v1_router = APIRouter(prefix="/v1")

# Include all v1 sub-routers
v1_router.include_router(users_router)
