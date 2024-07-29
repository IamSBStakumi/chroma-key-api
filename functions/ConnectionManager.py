from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections = websocket

    def disconnect(self) -> None:
        self.active_connections.clear()

    async def send_message(self, msg: str) -> None:
        await self.active_connections.send_json({"progress": msg})
