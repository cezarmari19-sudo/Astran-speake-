from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    full_id: Mapped[str] = mapped_column(String(20), primary_key=True, index=True)
    display_id: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(10), nullable=False, default="Anonim")
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )