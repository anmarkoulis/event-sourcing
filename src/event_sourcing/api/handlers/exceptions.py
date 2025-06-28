from fastapi import FastAPI


def configure_exception_handlers(app: FastAPI) -> None:
    """
    Configures the global exception handlers for the application.
    """
