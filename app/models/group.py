from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base

# Tabel de asociere Many-to-Many: grupuri ↔ membri
group_members = Table(
    "group_members",
    Base.metadata,
    Column("group_id", String(20), ForeignKey("groups.group_id"), primary_key=True),
    Column("user_id", String(20), ForeignKey("users.full_id"), primary_key=True),
    Column("is_admin", String(1), default="0"),
    Column("can_send", String(1), default="1"),
)


class Group(Base):
    """
    Grupuri cu control granular al permisiunilor.
    Admin poate restricționa cine trimite mesaje.
    """
    __tablename__ = "groups"

    group_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    display_id: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    admin_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.full_id"), nullable=False)
    only_admin_can_send: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )