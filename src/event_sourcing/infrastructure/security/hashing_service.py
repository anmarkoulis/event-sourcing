"""Password hashing service."""

from abc import ABC, abstractmethod

from passlib.context import CryptContext

from event_sourcing.infrastructure.enums import HashingMethod


class HashingServiceInterface(ABC):
    """Interface for password hashing services."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a plain text password.

        :param password: Plain text password.
        :return: Hashed password.
        """
        raise NotImplementedError()

    @abstractmethod
    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """Verify a plain text password against a hash.

        :param plain_password: Plain text password to verify.
        :param hashed_password: Hashed password to verify against.
        :return: True if password matches hash.
        """
        raise NotImplementedError()


class BcryptHashingService(HashingServiceInterface):
    """Bcrypt-based password hashing service."""

    def __init__(self) -> None:
        """Initialize bcrypt hashing service."""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.hashing_method = HashingMethod.BCRYPT

    def hash_password(self, password: str) -> str:
        """Hash a plain text password using bcrypt.

        :param password: Plain text password.
        :return: Hashed password.
        """
        return str(self.pwd_context.hash(password))

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """Verify a plain text password against a bcrypt hash.

        :param plain_password: Plain text password to verify.
        :param hashed_password: Hashed password to verify against.
        :return: True if password matches hash.
        """
        return bool(self.pwd_context.verify(plain_password, hashed_password))

    def get_hashing_method(self) -> HashingMethod:
        """Get the hashing method used by this service.

        :return: Hashing method identifier.
        """
        return self.hashing_method
