from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from database.db import db_dependency
from sqlmodel import select
from starlette import status
from pydantic import BaseModel
from database.models import Usuario, ChatsPadrao, UsuariosChatPadrao, Seguidores

class SeguidorController:
    async def lista_seguindo(id, quantidade, db: db_dependency):
        try:
            query = select(Usuario.id, Usuario.nome).join(Seguidores, Seguidores.usuario_seguido_id == Usuario.id).where(Seguidores.usuario_seguidor_id == id).limit(quantidade)
            result = db.exec(query).all()
            usuarios = []
            for i in result:
                usuarios.append({
                    "id":i[0],
                    "nome":i[1]
                })
            return JSONResponse(content=usuarios)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao retornar usuários")