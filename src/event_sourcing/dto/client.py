from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from .base import ModelConfigBaseModel


class ClientDTO(ModelConfigBaseModel):
    """Client data transfer object - core business fields only"""
    
    id: Optional[str] = None
    name: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: Optional[bool] = None
    
    class Config:
        from_attributes = True 