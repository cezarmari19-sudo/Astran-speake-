from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator
from ..core.database import get_db
from ..core.security import validate_full_id
from ..services.delivery import deliver_or_queue

router = APIRouter(prefix="/messages", tags=["messages"])


class SendMessageRequest(BaseModel):
    sender_id: str
    recipient_id: str
    encrypted_payload: str
    message_type: str = "text"

    @field_validator("sender_id", "recipient_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not validate_full_id(v):
            raise ValueError("ID invalid")
        return v

    @field_validator("message_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("text", "signal"):
            raise ValueError("message_type trebuie să fie 'text' sau 'signal'")
        return v


@router.post("/send")
async def send_message(req: SendMessageRequest, db: AsyncSession = Depends(get_db)):
    """
    Endpoint REST pentru trimitere mesaj.
    Serverul primește doar payload criptat E2EE — nu poate citi conținutul.
    """
    if req.sender_id == req.recipient_id:
        raise HTTPException(status_code=400, detail="Nu poți trimite mesaj ție însuți")

    result = await deliver_or_queue(
        db=db,
        sender_id=req.sender_id,
        recipient_id=req.recipient_id,
        encrypted_payload=req.encrypted_payload,
        message_type=req.message_type,
    )
    return result
