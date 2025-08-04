from sqlalchemy import DateTime
from sqlalchemy.orm import mapped_column


class DeletedAtMixin:
    """Mixin to add deleted_at timestamp field for soft deletes"""

    deleted_at = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=None,
        sort_order=1002,
    )
