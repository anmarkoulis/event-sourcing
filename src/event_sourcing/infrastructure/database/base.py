from typing import Any
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import as_declarative, declared_attr
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Generate __tablename__ automatically
    @declared_attr  # type: ignore[arg-type]
    def __tablename__(cls) -> str:  # pylint: disable=no-self-argument
        return cls.__name__.lower() 