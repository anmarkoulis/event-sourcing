from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from .backfill import backfill_router
from .clients import clients_router
from .events import events_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(events_router)
api_router.include_router(clients_router)
api_router.include_router(backfill_router)


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
