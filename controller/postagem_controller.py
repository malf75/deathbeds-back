from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from database.db import get_db
from sqlmodel import Session, select
from starlette import status
from typing import Annotated
from pydantic import BaseModel
from database.models import Postagem, Usuario
from datetime import datetime

db_dependency = Annotated[Session, Depends(get_db)]

class PostagemController:
  async def posta(id, corpo, db: db_dependency):
    try:
      postagem = Postagem(
        corpo=corpo,
        usuario_id=id,
      )
      db.add(postagem)
      db.commit()
      return JSONResponse(status_code=status.HTTP_201_CREATED, content='Postagem criada com sucesso!')
    except Exception as e:
      print(e)
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Erro ao realizar postagem!')
  
  async def lista_postagens(quantidade, db: db_dependency):
    try:
      query = select(Postagem, Usuario.nome).join(Usuario, Postagem.usuario_id == Usuario.id).offset(0).limit(quantidade).order_by(Postagem.criado_em.desc())
      response = db.exec(query).all()
      print(response)
      postagens = []
      for x in response:
        postagens.append({
          "id": x.Postagem.id,
          "usuario": x[1],
          "corpo": x.Postagem.corpo,
          "criado_em": x.Postagem.criado_em.strftime("%d/%m/%Y, %H:%M:%S")
        })
      return JSONResponse(content=postagens)
    except Exception as e:
      print(e)
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Erro ao listar postagem')