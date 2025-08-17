import re

from sqlalchemy.orm import DeclarativeBase, declared_attr


class BaseModel(DeclarativeBase):
    """Base model with common fields"""

    __abstract__ = True

    # Generate __tablename__ automatically in snake_case
    @declared_attr  # type: ignore[arg-type]
    def __tablename__(cls) -> str:  # pylint: disable=no-self-argument
        # Convert CamelCase to snake_case
        name = cls.__name__
        # First, insert underscore before any uppercase letter that follows a lowercase letter
        name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
        # Then, insert underscore before any uppercase letter that follows another uppercase letter
        name = re.sub(r"([A-Z])([A-Z][a-z])", r"\1_\2", name)
        return name.lower()
