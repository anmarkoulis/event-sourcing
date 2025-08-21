import logging

from event_sourcing.application.projections.base import Projection
from event_sourcing.dto import EventDTO
from event_sourcing.exceptions import EmailProjectionError
from event_sourcing.infrastructure.providers.email import (
    EmailProviderInterface,
)

logger = logging.getLogger(__name__)


class UserCreatedEmailProjection(Projection):
    """Email projection for handling USER_CREATED events"""

    def __init__(self, email_provider: EmailProviderInterface):
        """Initialize the email projection.

        :param email_provider: Email provider to use for sending emails.
        """
        self.email_provider = email_provider

    async def handle(self, event: EventDTO) -> None:
        """Handle USER_CREATED event by sending welcome email.

        :param event: The USER_CREATED event to handle.
        """
        try:
            # Extract user data from event
            user_email = event.data.email
            user_first_name = event.data.first_name
            user_last_name = event.data.last_name
            user_username = event.data.username

            # Create welcome email content
            subject = "Welcome to Our Platform!"
            body = self._create_welcome_email_body(
                first_name=user_first_name,
                last_name=user_last_name,
                username=user_username,
            )

            # Send welcome email
            success = await self.email_provider.send_email(
                to_email=user_email,
                subject=subject,
                body=body,
                from_email="welcome@example.com",
            )

            if success:
                logger.debug(
                    "Welcome email sent successfully to user: %s",
                    event.aggregate_id,
                )
            else:
                logger.error(
                    "Failed to send welcome email to user: %s",
                    event.aggregate_id,
                )
                raise EmailProjectionError(
                    "Welcome email sending failed for USER_CREATED event",
                    details={"email_type": "welcome", "recipient": user_email},
                    email_type="welcome",
                    recipient=user_email,
                )

        except Exception as e:
            logger.error(f"Error in UserCreatedEmailProjection: {e}")
            raise

    def _create_welcome_email_body(
        self, first_name: str, last_name: str, username: str
    ) -> str:
        """Create the welcome email body content.

        :param first_name: User's first name.
        :param last_name: User's last name.
        :param username: User's username.
        :return: Formatted email body content.
        """
        full_name = f"{first_name} {last_name}".strip()
        display_name = full_name if full_name else username

        return f"""
Dear {display_name},

Welcome to our platform! We're excited to have you on board.

Your account has been successfully created with the username: {username}

Here are some things you can do to get started:
- Complete your profile
- Explore our features
- Check out our documentation

If you have any questions, please don't hesitate to contact our support team.

Best regards,
The Team
        """.strip()
