from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from src.db.mixins.base import Base, BaseModel


class User(Base, BaseModel):
    __tablename__ = "tbl_users"

    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    registerd: Mapped[bool] = mapped_column(Boolean, default=False)
