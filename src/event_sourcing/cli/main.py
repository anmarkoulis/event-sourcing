"""Main CLI entry point for Event Sourcing application."""

import logging.config

import typer

from event_sourcing.config.settings import settings

from .users import users_app

# Configure logging using the same configuration as API and Celery
logging.config.dictConfig(settings.LOGGING_CONFIG)

app = typer.Typer(
    name="event-sourcing",
    help="Event Sourcing application CLI",
    add_completion=False,
)

# Add users package to main app
app.add_typer(users_app)

if __name__ == "__main__":  # pragma: no cover
    app()
