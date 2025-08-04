from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column


class UUIDIdMixin:
    """Mixin to add UUID primary key to models"""

    id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        server_default=func.gen_random_uuid(),
        sort_order=-1,
    )
