"""
Trimitere mesaj criptat E2EE. Serverul primește doar payload deja criptat —
nu poate citi conținutul niciunui mesaj.

Vechiul request accepta orice sender_id cu format valid, fără verificare —
oricine putea trimite mesaje care păreau să vină de la altcineva.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator
from ..core.database import get_db
from ..core.security import validate_full_id
from ..services.identity import verify_owner
from ..services.delivery import deliver_or_queue
from ..models.user import User

router = APIRouter(prefix="/messages", tags=["messages"])


class SendMessageRequest(BaseModel):
    sender_id: str
    sender_username: str
    recipient_id: str
    encrypted_payload: str
    message_type: str = "text"

    @field_validator("sender_id", "recipient_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not validate_full_id(v):
            raise ValueError("ID invalid")
        return v

    @field_validator("sender_username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 10:
            raise ValueError("sender_username invalid")
        return v

    @field_validator("message_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("text", "signal"):
            raise ValueError("message_type trebuie să fie 'text' sau 'signal'")
        return v

    @field_validator("encrypted_payload")
    @classmethod
    def validate_payload(cls, v: str) -> str:
        if not v:
            raise ValueError("encrypted_payload gol")
        return v


@router.post("/send")
async def send_message(req: SendMessageRequest, db: AsyncSession = Depends(get_db)):
    if req.sender_id == req.recipient_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="CANNOT_MESSAGE_SELF")

    sender = await verify_owner(db, req.sender_id, req.sender_username)
    if sender is None:
        # 401, nu 404 — nu confirmăm dacă sender_id există, doar că
        # perechea (id, username) prezentată nu e validă.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="SENDER_NOT_VERIFIED")

    recipient = await db.get(User, req.recipient_id)
    if recipient is None:
        # Fără verificarea asta, trimiterea către un ID inexistent pica
        # cu 500 (violare foreign key) doar dacă destinatarul era offline —
        # inconsistent și netratat.
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="RECIPIENT_NOT_FOUND")

    return await deliver_or_queue(
        db=db,
        sender_id=req.sender_id,
        recipient_id=req.recipient_id,
        encrypted_payload=req.encrypted_payload,
        message_type=req.message_type,
    )