from fastapi import FastAPI
from event_sourcing.api.handlers import (
    configure_logging,
    configure_exception_handlers,
    configure_middlewares,
    configure_routers,
    configure_openapi_tags,
    configure_lifespan,
)
from event_sourcing.config.settings import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENABLE_SWAGGER else None,
    description=settings.DESCRIPTION,
    debug=settings.DEBUG,
    contact={
        "name": "Antonis Markoulis",
        "email": "anmarkoulis@gmail.com",
    },
    openapi_tags=configure_openapi_tags(),
    version=settings.VERSION,
    servers=[{"url": "/"}],
    lifespan=configure_lifespan,
)

configure_logging()
configure_exception_handlers(app)
configure_middlewares(app)
configure_routers(app)
