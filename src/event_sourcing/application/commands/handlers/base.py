from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# Type variable for commands
CommandType = TypeVar("CommandType")


class CommandHandler(ABC, Generic[CommandType]):
    """Base interface for command handlers"""

    @abstractmethod
    async def handle(self, command: CommandType) -> None:
        """Handle a command"""
