from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"Usuário {user_id} conectado.")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"Usuário {user_id} desconectado.")

    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
        else:
            print(f"Tentativa de envio para usuário não conectado: {user_id}")
