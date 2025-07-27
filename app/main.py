import os
import uvicorn
from setup.settings import app
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from database.db import engine
from sqlmodel import SQLModel, Session
from auth.auth import router
from requests_.postagem_request import *
from controller.postagem_controller import *
from sockets.websocket import WebSocketManager

app.include_router(router)
SQLModel.metadata.create_all(engine)
db_dependency = Annotated[Session, Depends(get_db)]
manager = WebSocketManager()

@app.get("/")
def redirect_index():
    return RedirectResponse("/docs")

@app.get("/postagens")
async def lista(quantidade: int, db:db_dependency):
    postagens = await PostagemController.lista_postagens(quantidade, db)
    return postagens

@app.post("/postagens")
async def cria_postagem(request: CriaPostagemRequest, db: db_dependency):
    postagem = await PostagemController.posta(request.id, request.corpo, db)
    return postagem

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            to_user = data.get("to")
            if to_user:
                await manager.send_to_user(to_user, data)
    except WebSocketDisconnect:
        manager.disconnect(user_id)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)