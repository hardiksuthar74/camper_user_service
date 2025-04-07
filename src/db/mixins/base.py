from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import UUID
from sqlalchemy.dialects import postgresql as pg


from src.db.mixins.time_mixin import TimestampMixin
from src.db.mixins.user_mixin import UserTrackingMixin
from src.db.mixins.soft_delete_mixin import SoftDeleteMixin
from src.db.mixins.status_mixin import StatusMixin


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(
        pg.UUID(as_uuid=True),
        primary_key=True,
        default=UUID,
    )


class BaseModel(TimestampMixin, UserTrackingMixin, StatusMixin, SoftDeleteMixin):
    __abstract__ = True
