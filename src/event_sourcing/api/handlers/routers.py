from fastapi import FastAPI

from event_sourcing.api.routers.api_router import api_router


def configure_routers(app: FastAPI) -> None:
    """
    Configures the application's API routers.
    """
    app.include_router(api_router)
