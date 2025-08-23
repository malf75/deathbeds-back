import os
import uvicorn
from setup.settings import app
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, JSONResponse
from database.db import engine, db_dependency
from sqlmodel import SQLModel
from auth.auth import router
from typing import Optional
from requests_.postagem_request import *
from requests_.chat_request import *
from controller.postagem_controller import *
from controller.chat_controller import *
from sockets.websocket import WebSocketManager
from controller.seguidor_controller import *

app.include_router(router)
SQLModel.metadata.create_all(engine)
manager = WebSocketManager()

@app.get("/")
def redirect_index():
    return RedirectResponse("/docs")

@app.get("/postagens")
async def lista(quantidade: int, db:db_dependency):
    postagens = await PostagemController.lista(quantidade, db)
    return postagens

@app.post("/postagens")
async def cria_postagem(request: CriaPostagemRequest, db: db_dependency):
    postagem = await PostagemController.novo(request.id, request.corpo, db)
    return postagem

@app.get("/chat")
async def retorna_chat(usuario_id: int, chat_id: int, quantidade: int, db:db_dependency):
    chat = await ChatController.retorna_chat(usuario_id, chat_id, quantidade, db)
    return chat

@app.get("/chats")
async def retorna_chats(usuario_id: int, quantidade: int, db: db_dependency):
    chats = await ChatController.lista(usuario_id, quantidade, db)
    return chats

@app.post("/chats")
async def cria_chat(request: CriaChatRequest, db: db_dependency):
    chat = await ChatController.novo(request.usuario_id, request.destinatarios_id, request.nome, db)
    return chat

@app.get("/seguindo")
async def retorna_seguindo(usuario_id: int, quantidade: int, db: db_dependency):
    lista = await SeguidorController.lista_seguindo(usuario_id, quantidade, db)
    return lista

@app.websocket("/ws/{access_token}")
async def websocket_endpoint(websocket: WebSocket, access_token: str, db: db_dependency,  destinatario_id: Optional[int] = None):
    await manager.conecta(access_token, websocket, db)
    try:
        while True:
            response = await websocket.receive_json()
            tipo = response.get("type")
            print(tipo)
            print(response)
            if tipo == "notificacao":
                pass
            if tipo == "oferta":
                pass
            if tipo == "mensagem":
                response = await manager.envia_mensagem(access_token, response["corpo"], response["id_chat"], db)
                print(response)
    except WebSocketDisconnect:
        manager.desconecta(access_token, db)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)