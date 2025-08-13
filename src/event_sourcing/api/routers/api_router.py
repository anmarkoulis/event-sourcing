from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from event_sourcing.api.routers.v1.router import v1_router

api_router = APIRouter()

# Include the v1 router (which has its own prefix)
api_router.include_router(v1_router)


@api_router.get("/ht/", description="Health check", tags=["health"])
async def health_check() -> dict:
    """
    Health check endpoint to indicate service status.
    """
    return {"status": "UP"}


@api_router.get("/", include_in_schema=False)
async def docs_redirect() -> RedirectResponse:
    """
    Redirects the root URL to the API docs.
    """
    return RedirectResponse(url="/docs")
