from fastapi import WebSocket

from functions import init_progress as ip


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        ip.init_progress()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections = websocket

    def disconnect(self, websocket: WebSocket) -> None:
        websocket.close()

    async def send_message(self, msg) -> None:
        await self.active_connections.send_json(msg)
