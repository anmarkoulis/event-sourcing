"""Main CLI entry point for Event Sourcing application."""

import typer

from .users import users_app

app = typer.Typer(
    name="event-sourcing",
    help="Event Sourcing application CLI",
    add_completion=False,
)

# Add users package to main app
app.add_typer(users_app)

if __name__ == "__main__":
    app()
