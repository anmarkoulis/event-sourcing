from fastapi import FastAPI
from event_sourcing.api.middlewares import RequestLoggingMiddleware
from event_sourcing.config.settings import settings
from fastapi.middleware.trustedhost import TrustedHostMiddleware


from fastapi.middleware.cors import CORSMiddleware

def configure_middlewares(app: FastAPI) -> None:
    """
    Configures custom middlewares for the application.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS
    )
