import uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr


class UserTrackingMixin:
    """Mixin for adding created_by and updated_by fields using UUID (without foreign key)."""

    @declared_attr
    def created_by(cls):
        return Column(UUID(as_uuid=True), nullable=True, default=uuid.uuid4)

    @declared_attr
    def updated_by(cls):
        return Column(UUID(as_uuid=True), nullable=True)
