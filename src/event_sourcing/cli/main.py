"""Main CLI entry point for Event Sourcing application."""

import typer

from .create_admin import app as create_admin_app

app = typer.Typer(
    name="event-sourcing",
    help="Event Sourcing application CLI",
    add_completion=False,
)

# Add subcommands
app.add_typer(create_admin_app, name="create-admin", help="Create admin user")

if __name__ == "__main__":
    app()
