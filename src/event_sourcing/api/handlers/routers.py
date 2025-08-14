from fastapi import FastAPI

from event_sourcing.api.routers.api_router import api_router


def configure_routers(app: FastAPI) -> None:
    """
    Configures the application's API routers.
    """
    # Include the main API router (which includes v1 and non-versioned endpoints)
    app.include_router(api_router)
