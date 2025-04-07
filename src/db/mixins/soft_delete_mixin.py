from sqlalchemy import Column, Boolean
from sqlalchemy.orm import declared_attr


class SoftDeleteMixin:
    """Mixin to add soft delete functionality to a SQLAlchemy model.

    Adds an 'is_deleted' boolean column to indicate whether the record
    has been logically deleted (without actually removing it from the database).

    """

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, nullable=False, default=False)
