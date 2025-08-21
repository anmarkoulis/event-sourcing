"""Business rule violation domain exceptions."""

from typing import Optional

from .base import EventSourcingError


class BusinessRuleViolationError(EventSourcingError):
    """Exception raised when business rules are violated."""

    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, details)
        self.rule_name = rule_name


class UserBusinessRuleViolationError(BusinessRuleViolationError):
    """Exception raised when user business rules are violated."""


class CannotUpdateDeletedUserError(UserBusinessRuleViolationError):
    """Exception raised when trying to update a deleted user."""

    def __init__(self, user_id: str) -> None:
        super().__init__(
            f"Cannot update deleted user: {user_id}",
            "user_update_deleted",
            {"user_id": user_id},
        )


class CannotChangePasswordForDeletedUserError(UserBusinessRuleViolationError):
    """Exception raised when trying to change password for a deleted user."""

    def __init__(self, user_id: str) -> None:
        super().__init__(
            f"Cannot change password for deleted user: {user_id}",
            "password_change_deleted",
            {"user_id": user_id},
        )


class UserAlreadyDeletedError(UserBusinessRuleViolationError):
    """Exception raised when trying to delete an already deleted user."""

    def __init__(self, user_id: str) -> None:
        super().__init__(
            f"User {user_id} is already deleted",
            "user_already_deleted",
            {"user_id": user_id},
        )
