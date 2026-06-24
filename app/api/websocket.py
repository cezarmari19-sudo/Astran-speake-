from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.database import AsyncSessionFactory
from ..core.security import validate_full_id
from ..services.connection_manager import manager
from ..services.delivery import flush_offline_queue, deliver_or_queue
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{full_id}")
async def websocket_endpoint(full_id: str, websocket: WebSocket):
    """
    Hub WebSocket Zero-Knowledge:
    - Autentificare prin validarea full_id (20 chars)
    - La conectare: flush automat al cozii offline
    - Mesaje live: routing direct prin RAM (fără persistență)
    - La deconectare: cleanup instant din memoria activă
    """
    if not validate_full_id(full_id):
        await websocket.close(code=4001, reason="ID invalid")
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

                async with AsyncSessionFactory() as db:
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

    except WebSocketDisconnect:
        manager.disconnect(full_id)
        logger.info(f"Client deconectat: {full_id[:7]}... | Total online: {manager.online_count()}")