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

    async def envia_mensagem(self, access_token: str, corpo: str, id_chat: int, tipo_chat: str, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        participantes = await ChatController.retorna_usuarios_participantes(id_chat, tipo_chat, db)
        try:
            if usuario["id"] in participantes:
                mensagem = await ChatController.cria_mensagem(usuario["id"], id_chat, corpo, tipo_chat, db)
                # chat = await ChatController.retorna_chat(usuario["id"], id_chat, 0, db)
                for p in participantes:
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
        
    async def encaminha_oferta(self, access_token: str, destinatario_id: int, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        try:
            if usuario:
                await self.conexoes_ativas[destinatario_id].send_json({
                    "type": "call_request",
                    "destino_id": usuario["id"],
                    "destino": usuario["nome"]
                })
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao encaminhar chamada ao usuário")

    async def cancela_oferta(self, access_token: str, destinatario_id: int, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        try:
            if usuario:
                await self.conexoes_ativas[destinatario_id].send_json({
                    "type": "call_request_cancelled",
                    "destino_id": usuario["id"]
                })
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao cancelar chamada")
        
    async def rejeita_oferta(self, access_token: str, destinatario_id: int, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        try:
            if usuario:
                await self.conexoes_ativas[destinatario_id].send_json({
                    "type": "call_request_rejected",
                    "destino_id": usuario["id"]
                })
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao cancelar chamada")
    
    async def aceita_oferta(self, access_token: str, destinatario_id: int, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        participantes = [usuario["id"], destinatario_id]
        try:
            if usuario:
                for p in participantes:
                  await self.conexoes_ativas[p].send_json({
                      "type": "call_request_accepted",
                      "destino_id": usuario["id"],
                      "destinatario_id": destinatario_id
                  })
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao aceitar chamada")
        
    async def encaminha_oferta_p2p(self, access_token: str, destinatario_id: int, oferta: object, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        try:
            if usuario:
                await self.conexoes_ativas[destinatario_id].send_json({
                    "type": "offer",
                    "from": usuario["id"],
                    "to": destinatario_id,
                    "offer": oferta
                })
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao enviar oferta p2p")
        
    async def responde_oferta_p2p(self, access_token: str, destinatario_id: int, resposta: object, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        try:
            if usuario:
                await self.conexoes_ativas[destinatario_id].send_json({
                    "type": "answer",
                    "from": usuario["id"],
                    "to": destinatario_id,
                    "answer": resposta
                })
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao enviar oferta p2p")
    
    async def envia_icecandidate(self, access_token: str, destinatario_id: int, candidate: object, db: db_dependency):
        usuario = await get_current_user(access_token, db)
        try:
            if usuario:
                await self.conexoes_ativas[destinatario_id].send_json({
                    "type": "candidate",
                    "from": usuario["id"],
                    "to": destinatario_id,
                    "candidate": candidate
                })
        except Exception as e:
            print(e)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao enviar oferta p2p")
        
