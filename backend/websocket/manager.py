import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications.
    Usa asyncio.Lock para prevenir race conditions en acceso concurrente."""

    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

    async def disconnect(self, websocket: WebSocket, user_id: str):
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a specific user"""
        async with self._lock:
            connections = list(self.active_connections.get(user_id, []))
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
                disconnected.append(connection)
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if user_id in self.active_connections:
                        self.active_connections[user_id].discard(conn)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        async with self._lock:
            user_ids = list(self.active_connections.keys())
        for user_id in user_ids:
            await self.send_to_user(user_id, message)


# Instancia global del manager
ws_manager = ConnectionManager()
