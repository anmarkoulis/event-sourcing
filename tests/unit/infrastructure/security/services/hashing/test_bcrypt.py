"""Tests for Bcrypt hashing service."""

import pytest

from event_sourcing.infrastructure.security import BcryptHashingService


class TestBcryptHashingService:
    """Test cases for BcryptHashingService."""

    @pytest.fixture
    def hashing_service(self) -> BcryptHashingService:
        """Provide a BcryptHashingService instance."""
        return BcryptHashingService()

    def test_init(self, hashing_service: BcryptHashingService) -> None:
        """Test service initialization."""
        assert hashing_service is not None

    def test_hash_password(
        self, hashing_service: BcryptHashingService
    ) -> None:
        """Test password hashing."""
        password = "testpassword123"  # noqa: S105  # pragma: allowlist secret
        hashed = hashing_service.hash_password(password)

        # Hash should be different from original password
        assert hashed != password
        # Hash should be a string
        assert isinstance(hashed, str)
        # Hash should be longer than original password
        assert len(hashed) > len(password)

    def test_verify_password_correct(
        self, hashing_service: BcryptHashingService
    ) -> None:
        """Test password verification with correct password."""
        password = "testpassword123"  # noqa: S105  # pragma: allowlist secret
        hashed = hashing_service.hash_password(password)

        assert hashing_service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(
        self, hashing_service: BcryptHashingService
    ) -> None:
        """Test password verification with incorrect password."""
        password = "testpassword123"  # noqa: S105  # pragma: allowlist secret
        hashed = hashing_service.hash_password(password)

        assert (
            hashing_service.verify_password("wrongpassword", hashed) is False
        )
