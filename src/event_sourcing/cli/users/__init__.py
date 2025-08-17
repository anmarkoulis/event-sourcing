"""Users package for CLI user management commands."""

import typer

from .create_admin import create_admin

# Create users subcommand group
users_app = typer.Typer(name="users", help="User management commands")

# Add all user commands to the users app
users_app.command(name="create-admin", help="Create admin user")(create_admin)


__all__ = ["users_app"]
