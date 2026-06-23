from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class OfflineMessage(Base):
    """
    Coadă temporară pentru mesaje când destinatarul e offline.
    ȘTERS IMEDIAT după livrare sau după 14 zile — Zero-Knowledge garantat.
    Payload-ul e deja criptat E2EE pe client — serverul nu poate citi nimic.
    """
    __tablename__ = "offline_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sender_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    recipient_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.full_id"), index=True)
    encrypted_payload: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(10), default="text")  # text | signal
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
