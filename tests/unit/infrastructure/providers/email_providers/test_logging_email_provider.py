from unittest.mock import patch

import pytest

from event_sourcing.infrastructure.providers.email import LoggingEmailProvider


class TestLoggingEmailProvider:
    """Test cases for LoggingEmailProvider"""

    @pytest.fixture
    def provider(self) -> LoggingEmailProvider:
        """Create a LoggingEmailProvider instance"""
        return LoggingEmailProvider()

    @pytest.fixture
    def provider_with_config(self) -> LoggingEmailProvider:
        """Create a LoggingEmailProvider instance with custom config"""
        config = {"default_from_email": "custom@example.com"}
        return LoggingEmailProvider(config=config)

    @pytest.mark.asyncio
    async def test_send_email_logs_email_details(
        self, provider: LoggingEmailProvider
    ) -> None:
        """Test that send_email logs the email details"""
        with patch(
            "event_sourcing.infrastructure.providers.email.logging_email_provider.logger"
        ) as mock_logger:
            # Act
            result = await provider.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                body="Test Body",
                from_email="sender@example.com",
            )

            # Assert
            assert result is True
            assert mock_logger.info.call_count == 2  # Two log calls

            # Check first log call (structured logging)
            first_call = mock_logger.info.call_args_list[0]
            assert first_call[0][0] == "EMAIL WOULD BE SENT:"
            assert first_call[1]["extra"]["to_email"] == "test@example.com"
            assert first_call[1]["extra"]["subject"] == "Test Subject"
            assert first_call[1]["extra"]["body"] == "Test Body"
            assert first_call[1]["extra"]["from_email"] == "sender@example.com"

            # Check second log call (readable format)
            second_call = mock_logger.info.call_args_list[1]
            assert "📧 Email logged (not sent):" in second_call[0][0]
            assert "From: sender@example.com" in second_call[0][0]
            assert "To: test@example.com" in second_call[0][0]
            assert "Subject: Test Subject" in second_call[0][0]

    @pytest.mark.asyncio
    async def test_send_email_uses_default_from_email(
        self, provider: LoggingEmailProvider
    ) -> None:
        """Test that send_email uses default from_email when not provided"""
        with patch(
            "event_sourcing.infrastructure.providers.email.logging_email_provider.logger"
        ) as mock_logger:
            # Act
            await provider.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                body="Test Body",
            )

            # Assert
            first_call = mock_logger.info.call_args_list[0]
            assert (
                first_call[1]["extra"]["from_email"] == "noreply@example.com"
            )

    @pytest.mark.asyncio
    async def test_send_email_uses_custom_default_from_email(
        self, provider_with_config: LoggingEmailProvider
    ) -> None:
        """Test that send_email uses custom default from_email from config"""
        with patch(
            "event_sourcing.infrastructure.providers.email.logging_email_provider.logger"
        ) as mock_logger:
            # Act
            await provider_with_config.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                body="Test Body",
            )

            # Assert
            first_call = mock_logger.info.call_args_list[0]
            assert first_call[1]["extra"]["from_email"] == "custom@example.com"

    @pytest.mark.asyncio
    async def test_send_email_with_additional_parameters(
        self, provider: LoggingEmailProvider
    ) -> None:
        """Test that send_email handles additional parameters"""
        with patch(
            "event_sourcing.infrastructure.providers.email.logging_email_provider.logger"
        ) as mock_logger:
            # Act
            await provider.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                body="Test Body",
                cc="cc@example.com",
                bcc="bcc@example.com",
                reply_to="reply@example.com",
            )

            # Assert
            first_call = mock_logger.info.call_args_list[0]
            additional_params = first_call[1]["extra"]["additional_params"]
            assert additional_params["cc"] == "cc@example.com"
            assert additional_params["bcc"] == "bcc@example.com"
            assert additional_params["reply_to"] == "reply@example.com"

    def test_get_provider_name(self, provider: LoggingEmailProvider) -> None:
        """Test that get_provider_name returns the correct name"""
        assert provider.get_provider_name() == "logging"

    def test_is_available(self, provider: LoggingEmailProvider) -> None:
        """Test that is_available always returns True"""
        assert provider.is_available() is True

    def test_get_config(self, provider: LoggingEmailProvider) -> None:
        """Test that get_config returns the configuration"""
        config = provider.get_config()
        assert isinstance(config, dict)
        assert "default_from_email" in config
        assert config["default_from_email"] == "noreply@example.com"

    def test_get_config_with_custom_config(
        self, provider_with_config: LoggingEmailProvider
    ) -> None:
        """Test that get_config returns the custom configuration"""
        config = provider_with_config.get_config()
        assert isinstance(config, dict)
        assert config["default_from_email"] == "custom@example.com"
