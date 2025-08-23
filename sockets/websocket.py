from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict
from auth.auth import get_current_user
from database.db import db_dependency
from fastapi.responses import JSONResponse
from starlette import status
from controller.chat_controller import ChatController

class WebSocketManager:
    def __init__(self):
        self.conexoes_ativas: Dict[str, WebSocket] = {}

    async def conecta(self, access_token: str, websocket: WebSocket, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        try:
            await websocket.accept()
            self.conexoes_ativas[usuario["id"]] = websocket
            self.conexoes_ativas[usuario["id"]].send_text("Usuário conectado ao WebSocket")
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao conectar usuário ao WebSocket")

    async def desconecta(self, access_token: str, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        try:
            if usuario["id"] in self.conexoes_ativas:
                del self.conexoes_ativas[usuario["id"]]
                return JSONResponse(status_code=status.HTTP_200_OK, content="Usuário desconectado do WebSocket")
            else:
                return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Usuário não está conectado ao WebSocket")
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao desconectar usuário do WebSocket")

    async def envia_mensagem(self, access_token: str, corpo: str, id_chat: int, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        participantes = await ChatController.retorna_usuarios_participantes(id_chat, db)
        try:
            if usuario["id"] in participantes:
                mensagem = await ChatController.cria_mensagem(usuario["id"], id_chat, corpo, db)
                chat = await ChatController.retorna_chat(usuario["id"], id_chat, 0, db)
                for p in participantes:
                    print(self.conexoes_ativas[p])
                    if p in self.conexoes_ativas:
                        await self.conexoes_ativas[p].send_json({
                            "type": "mensagem",
                            "id": mensagem.id,
                            "chat_id": mensagem.chat_id,
                            "usuario_id": mensagem.usuario_id,
                            "corpo": mensagem.corpo,
                            "criado_em": mensagem.criado_em.strftime("%d/%m/%Y, %H:%M:%S")
                        })
                        # await self.envia_notificacao(access_token, p, {"notificacao": f"Nova mensagem de {usuario.nome} em {chat.nome}"})
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao enviar mensagem para o usuário")
    
    async def envia_notificacao(self, access_token: str, destino: int, message: dict, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        try:
        # função do notificacao_controller
            if destino in self.conexoes_ativas:
                await self.conexoes_ativas[destino].send_json(message)
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao enviar notificação ao usuário")
    
    async def envia_icecandidate(self, access_token: str, destino: int, message: dict, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        try:
            if destino in self.conexoes_ativas:
                await self.conexoes_ativas[destino].send_json(message)
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao enviar icecandidate ao usuário")
        
