"""
Hub WebSocket Zero-Knowledge.

Vechea conectare verifica doar FORMATUL full_id-ului — orice șir cu formatul
corect putea "deveni" orice utilizator. Acum cere și username, verificat o
singură dată la conectare (nu la fiecare mesaj — mai eficient, și suficient,
fiindcă odată verificată, conexiunea WebSocket însăși e dovada de identitate
pentru toate mesajele trimise prin ea).
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..core.database import AsyncSessionFactory
from ..core.security import validate_full_id
from ..services.identity import verify_owner
from ..services.connection_manager import manager
from ..services.delivery import flush_offline_queue, deliver_or_queue
from ..models.user import User
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{full_id}")
async def websocket_endpoint(
    full_id: str,
    websocket: WebSocket,
    username: str = Query(..., min_length=1, max_length=10),
):
    if not validate_full_id(full_id):
        await websocket.close(code=4001, reason="ID invalid")
        return

    async with AsyncSessionFactory() as db:
        owner = await verify_owner(db, full_id, username)

    if owner is None:
        # 4003 = identitate neconfirmată, distinct de 4001 = format greșit —
        # clientul mobil poate distinge o eroare locală de credențiale greșite.
        await websocket.close(code=4003, reason="Identitate neconfirmată")
        return

    await manager.connect(full_id, websocket)
    logger.info(f"Client conectat: {full_id[:7]}... | Total online: {manager.online_count()}")

    async with AsyncSessionFactory() as db:
        delivered = await flush_offline_queue(db, full_id)
        if delivered > 0:
            logger.info(f"Livrate {delivered} mesaje offline pentru {full_id[:7]}...")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "JSON invalid"}))
                continue

            msg_type = data.get("type")

            if msg_type == "message":
                recipient_id = data.get("recipient_id", "")
                payload = data.get("payload", "")

                if not validate_full_id(recipient_id) or not payload:
                    await websocket.send_text(json.dumps({"error": "Date lipsă sau invalide"}))
                    continue

                if recipient_id == full_id:
                    await websocket.send_text(json.dumps({"error": "CANNOT_MESSAGE_SELF"}))
                    continue

                async with AsyncSessionFactory() as db:
                    recipient = await db.get(User, recipient_id)
                    if recipient is None:
                        await websocket.send_text(json.dumps({"error": "RECIPIENT_NOT_FOUND"}))
                        continue

                    result = await deliver_or_queue(
                        db=db,
                        sender_id=full_id,
                        recipient_id=recipient_id,
                        encrypted_payload=payload,
                        message_type=data.get("message_type", "text"),
                    )

                await websocket.send_text(json.dumps({"type": "ack", **result}))

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            else:
                await websocket.send_text(json.dumps({"error": "Tip mesaj necunoscut"}))

    except WebSocketDisconnect:
        manager.disconnect(full_id)
        logger.info(f"Client deconectat: {full_id[:7]}... | Total online: {manager.online_count()}")