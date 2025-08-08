from abc import ABC

import pytest

from event_sourcing.infrastructure.providers.email import (
    EmailProviderInterface,
)


class TestEmailProviderInterface:
    """Test cases for EmailProviderInterface"""

    def test_is_abstract_base_class(self) -> None:
        """Test that EmailProviderInterface is an abstract base class"""
        assert issubclass(EmailProviderInterface, ABC)

    def test_has_required_abstract_methods(self) -> None:
        """Test that EmailProviderInterface has required abstract methods"""
        # Check that the class has the required abstract methods
        assert hasattr(EmailProviderInterface, "send_email")
        assert hasattr(EmailProviderInterface, "get_provider_name")
        assert hasattr(EmailProviderInterface, "is_available")

    def test_has_optional_methods(self) -> None:
        """Test that EmailProviderInterface has optional methods"""
        # Check that the class has optional methods
        assert hasattr(EmailProviderInterface, "get_config")

    def test_cannot_instantiate_interface(self) -> None:
        """Test that EmailProviderInterface cannot be instantiated directly"""
        with pytest.raises(TypeError):
            EmailProviderInterface()

    def test_interface_method_signatures(self) -> None:
        """Test that interface methods have correct signatures"""
        # Check send_email method signature
        send_email_sig = EmailProviderInterface.send_email.__annotations__
        assert "to_email" in send_email_sig
        assert "subject" in send_email_sig
        assert "body" in send_email_sig
        assert "from_email" in send_email_sig
        assert send_email_sig["return"] == bool

        # Check get_provider_name method signature
        get_provider_name_sig = (
            EmailProviderInterface.get_provider_name.__annotations__
        )
        assert get_provider_name_sig["return"] == str

        # Check is_available method signature
        is_available_sig = EmailProviderInterface.is_available.__annotations__
        assert is_available_sig["return"] == bool

        # Check get_config method signature
        get_config_sig = EmailProviderInterface.get_config.__annotations__
        assert "return" in get_config_sig
