from datetime import datetime, timezone
from sqlalchemy import delete
from ..models.message import OfflineMessage
from ..core.database import AsyncSessionFactory
import logging

logger = logging.getLogger(__name__)


async def cleanup_expired_messages() -> int:
    """
    Job scheduler — rulează periodic și șterge mesajele expirate.
    Garanție arhitecturală: niciun mesaj nu supraviețuiește mai mult de 14 zile.
    """
    async with AsyncSessionFactory() as db:
        try:
            result = await db.execute(
                delete(OfflineMessage)
                .where(OfflineMessage.expires_at < datetime.now(timezone.utc))
            )
            await db.commit()
            count = result.rowcount
            if count > 0:
                logger.info(f"Cleanup: {count} mesaje expirate șterse")
            return count
        except Exception as e:
            logger.error(f"Eroare cleanup: {e}")
            await db.rollback()
            return 0