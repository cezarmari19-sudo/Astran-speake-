from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.message import OfflineMessage
from ..services.connection_manager import manager
from ..core.config import get_settings

settings = get_settings()


async def deliver_or_queue(
    db: AsyncSession,
    sender_id: str,
    recipient_id: str,
    encrypted_payload: str,
    message_type: str = "text",
) -> dict:
    payload = {
        "type": "message",
        "sender_id": sender_id,
        "payload": encrypted_payload,
        "message_type": message_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    delivered = await manager.send_to(recipient_id, payload)

    if delivered:
        return {"status": "delivered", "queued": False}

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.message_expiry_days)
    msg = OfflineMessage(
        sender_id=sender_id,
        recipient_id=recipient_id,
        encrypted_payload=encrypted_payload,
        message_type=message_type,
        expires_at=expires_at,
    )
    db.add(msg)
    await db.flush()
    return {"status": "queued", "queued": True, "expires_at": expires_at.isoformat()}


async def flush_offline_queue(db: AsyncSession, full_id: str) -> int:
    result = await db.execute(
        select(OfflineMessage)
        .where(OfflineMessage.recipient_id == full_id)
        .where(OfflineMessage.delivered == False)  # noqa: E712
        .order_by(OfflineMessage.created_at)
    )
    messages = result.scalars().all()
    delivered_count = 0

    for msg in messages:
        payload = {
            "type": "message",
            "sender_id": msg.sender_id,
            "payload": msg.encrypted_payload,
            "message_type": msg.message_type,
            "timestamp": msg.created_at.isoformat(),
            "was_queued": True,
        }
        success = await manager.send_to(full_id, payload)
        if success:
            await db.delete(msg)
            delivered_count += 1

    # FIX BUG 3: commit după ștergere — fără asta mesajele revin la reconectare
    if delivered_count > 0:
        await db.commit()

    return delivered_count