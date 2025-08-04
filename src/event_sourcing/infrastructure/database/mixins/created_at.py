from sqlalchemy import DateTime, func
from sqlalchemy.orm import mapped_column


class CreatedAtMixin:
    """Mixin to add created_at timestamp field to models"""

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        sort_order=1000,
    )
