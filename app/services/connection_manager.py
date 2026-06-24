from fastapi import WebSocket
from typing import Dict
import json


class ConnectionManager:
    """
    Manager WebSocket în memorie pură — Zero-Persistence by design.
    Dicționar full_id → WebSocket pentru routing direct O(1).
    Thread-safe prin asyncio (single-threaded event loop).
    """

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}

    async def connect(self, full_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[full_id] = websocket

    def disconnect(self, full_id: str) -> None:
        self._connections.pop(full_id, None)

    def is_online(self, full_id: str) -> bool:
        return full_id in self._connections

    async def send_to(self, full_id: str, payload: dict) -> bool:
        """
        Trimite mesaj direct în RAM dacă userul e online.
        Returnează True dacă livrarea a reușit, False dacă e offline.
        """
        ws = self._connections.get(full_id)
        if ws is None:
            return False
        try:
            await ws.send_text(json.dumps(payload))
            return True
        except Exception:
            self.disconnect(full_id)
            return False

    def online_count(self) -> int:
        return len(self._connections)


# Singleton global — o singură instanță per proces
manager = ConnectionManager()