"""Price snapshot table — global, no user_id."""
import datetime
from sqlalchemy import String, Float, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market_hash_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(16), nullable=False)  # csqaq | steamdt
    price: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    __table_args__ = (
        Index("idx_snapshot_item_time", "market_hash_name", "timestamp"),
    )
