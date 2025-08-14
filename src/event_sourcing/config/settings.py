from logging import getLogger
from typing import List

from environs import Env
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = getLogger(__name__)
env = Env()


def get_logging_config(log_level: str, log_format: str = "json") -> dict:
    return {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} {process} {thread} "
                "{pathname}:{funcName}:{lineno} - {message}",
                "style": "{",
            },
        },
        "handlers": {
            "event_sourcing": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "json" if log_format == "json" else "verbose",
            },
        },
        "loggers": {
            "event_sourcing": {
                "handlers": ["event_sourcing"],
                "level": log_level,
                "propagate": False,
            },
        },
    }


class CeleryConfig(BaseModel):
    timezone: str = "UTC"
    broker_url: str = env.str("CELERY_BROKER_URL")
    accept_content: List[str] = ["json"]
    task_serializer: str = "json"
    result_serializer: str = "json"
    task_time_limit: int = 5 * 60
    task_soft_time_limit: int = 60
    result_expires: int = 60 * 24 * 7
    result_backend: str = (
        f"db+{env.str('DATABASE_URL').replace('asyncpg', 'psycopg2')}"
    )
    broker_transport_options: dict = {
        # 'visibility_timeout': 3600,
        "polling_interval": 10,
        "wait_time_seconds": 10,  # valid values: 0 - 20
        # 'region': 'us-east-1'
        "predefined_queues": {
            "celery": {
                "url": env.str("CELERY_QUEUE_URL"),
            }
        },
    }
    broker_transport: str = "sqs"
    worker_send_task_events: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    ENV: str = env.str("ENV", "dev")
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "Event Sourcing"
    DESCRIPTION: str = "This is an example Event Sourcing project"
    VERSION: str = env.str("VERSION", "0.1.0")
    ENABLE_SWAGGER: bool = env.bool("ENABLE_SWAGGER", False)
    USE_AUTH: bool = env.bool("USE_AUTH", True)
    BACKEND_CORS_ORIGINS: List = env.list("BACKEND_CORS_ORIGINS")
    ALLOWED_HOSTS: List = env.list("ALLOWED_HOSTS")
    DATABASE_URL: str = env.str("DATABASE_URL", "")
    TEST_DATABASE_URL: str = DATABASE_URL.replace("event_sourcing", "test")
    SYNC_EVENT_HANDLER: bool = env.bool("SYNC_EVENT_HANDLER", False)
    # Celery
    # ------------------------------------------------------------------------------
    CELERY_CONFIG: CeleryConfig = CeleryConfig()
    DEBUG: bool = False
    LOGGING_CONFIG: dict = get_logging_config(
        env.str("LOGGING_LEVEL", "INFO"), env.str("LOGGING_FORMAT", "json")
    )


settings = Settings()
