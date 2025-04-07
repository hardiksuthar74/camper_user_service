from sqlalchemy import Column, Boolean
from sqlalchemy.orm import declared_attr


class StatusMixin:
    """Mixin to add a status flag to a SQLAlchemy model.

    Adds a 'status' boolean column to represent active/inactive state.
    Useful for toggling availability or visibility without deleting records.
    """

    @declared_attr
    def status(cls):
        return Column(Boolean, nullable=False, default=True)
