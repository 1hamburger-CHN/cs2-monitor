"""User table."""
import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    steam_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    steam_api_key_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    server_chan_key_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    preferred_source: Mapped[str] = mapped_column(String(16), default="csqaq")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
