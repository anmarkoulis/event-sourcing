"""Password hashing service interface."""

from abc import ABC, abstractmethod

from event_sourcing.enums import HashingMethod


class HashingServiceInterface(ABC):  # pragma: no cover
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

    @abstractmethod
    def get_hashing_method(self) -> HashingMethod:
        """Get the hashing method used by this service.

        :return: Hashing method identifier.
        """
        raise NotImplementedError()
