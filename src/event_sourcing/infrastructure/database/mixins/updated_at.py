from sqlalchemy import DateTime, func
from sqlalchemy.orm import mapped_column


class UpdatedAtMixin:
    """Mixin to add updated_at timestamp field to models"""

    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        sort_order=1001,
    )
