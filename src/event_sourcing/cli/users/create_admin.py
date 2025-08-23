"""CLI command to create an admin user from environment variables."""

import asyncio
import logging
import uuid
from typing import Optional

import typer
from environs import Env

from event_sourcing.application.commands.user.create_user import (
    CreateUserCommand,
)
from event_sourcing.cli.handlers.exception import cli_error_handler
from event_sourcing.config.settings import settings
from event_sourcing.enums import Role
from event_sourcing.exceptions import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from event_sourcing.infrastructure.provider import get_infrastructure_factory
from event_sourcing.utils import log_typer_command

logger = logging.getLogger(__name__)
env = Env()


def create_admin(
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Admin username"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Admin password"
    ),
    email: Optional[str] = typer.Option(
        None, "--email", "-e", help="Admin email"
    ),
    first_name: str = typer.Option(
        "Admin", "--first-name", "-f", help="Admin first name"
    ),
    last_name: str = typer.Option(
        "User", "--last-name", "-l", help="Admin last name"
    ),
) -> None:
    """Create an admin user from environment variables or command line arguments.

    Note: This command will attempt to create the admin user. If a user with the same
    username or email already exists, the command will fail with an appropriate error message.
    """

    # Use command line arguments if provided, otherwise fall back to environment variables
    admin_username = username or settings.ADMIN_USERNAME
    admin_password = password or settings.ADMIN_PASSWORD
    admin_email = email or settings.ADMIN_EMAIL

    typer.echo(f"Creating admin user:")
    typer.echo(f"  Username: {admin_username}")
    typer.echo(f"  Email: {admin_email}")
    typer.echo(f"  First Name: {first_name}")
    typer.echo(f"  Last Name: {last_name}")
    typer.echo(f"  Role: ADMIN")

    # Run the async function
    asyncio.run(
        create_admin_user(
            username=admin_username,
            password=admin_password,
            email=admin_email,
            first_name=first_name,
            last_name=last_name,
        )
    )


@cli_error_handler
@log_typer_command
async def create_admin_user(
    username: str,
    password: str,
    email: str,
    first_name: str,
    last_name: str,
) -> None:
    """Create an admin user asynchronously."""

    # Get infrastructure factory
    factory = get_infrastructure_factory()

    # Create command handler
    command_handler = factory.create_create_user_command_handler()

    # Create the command
    command = CreateUserCommand(
        user_id=uuid.uuid4(),
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password,
        role=Role.ADMIN,
    )

    # Execute the command with exception handling for domain errors
    try:
        await command_handler.handle(command)
        typer.echo(f"✅ Admin user '{username}' created successfully!")
        typer.echo(f"User ID: {command.user_id}")
    except (
        UsernameAlreadyExistsError,
        EmailAlreadyExistsError,
    ) as e:
        # Handle domain exceptions about duplicate users gracefully
        if isinstance(e, UsernameAlreadyExistsError):
            typer.echo(f"⚠️  User '{username}' already exists!")
        elif isinstance(e, EmailAlreadyExistsError):
            typer.echo(f"⚠️  User with email '{email}' already exists!")

        typer.echo("Admin user creation skipped - user already exists.")
        # Don't raise an exception, just return gracefully
        return
