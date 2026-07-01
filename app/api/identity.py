"""
Verificare de proprietate a identității: confirmă că o pereche (id, username)
aparține aceluiași utilizator înregistrat.

Separat de core/security.py (care face doar validări de format, fără DB —
ușor de testat unitar). Acest modul e stratul care atinge baza de date pentru
verificarea reală de proprietate, refolosit identic în users, messages,
websocket și groups — fără duplicare de logică.
"""
import hmac
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User


async def verify_owner(db: AsyncSession, full_id: str, username: str) -> User | None:
    """Verificare când clientul își cunoaște propriul full_id complet
    (conectare WebSocket, trimitere mesaj, creare/join grup)."""
    user = await db.get(User, full_id)
    if user is None:
        return None
    if not hmac.compare_digest(
        user.username.encode("utf-8"), username.strip().encode("utf-8")
    ):
        return None
    return user


async def resolve_by_display_id(db: AsyncSession, display_id: str, username: str) -> User | None:
    """Verificare când cineva ADAUGĂ un contact și cunoaște doar
    informația publică a celuilalt (7 caractere + nume), nu full_id-ul lui."""
    result = await db.execute(select(User).where(User.display_id == display_id))
    for user in result.scalars().all():
        if hmac.compare_digest(user.username.encode("utf-8"), username.strip().encode("utf-8")):
            return user
    return None