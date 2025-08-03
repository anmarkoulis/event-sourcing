import re
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, declared_attr

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase

    Base = DeclarativeBase
else:
    Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields"""

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    # Generate __tablename__ automatically in snake_case
    @declared_attr  # type: ignore[arg-type]
    def __tablename__(cls) -> str:  # pylint: disable=no-self-argument
        # Convert CamelCase to snake_case
        name = cls.__name__
        name = re.sub("(?!^)([A-Z][a-z]+)", r"_\1", name)
        name = re.sub("(?!^)([A-Z]+)", r"_\1", name)
        return name.lower()


class TimestampedModel(BaseModel):
    """Base model with timestamp fields"""

    __abstract__ = True

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
