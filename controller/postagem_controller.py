from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from starlette import status
from pydantic import BaseModel
from database.models import Postagem, Usuario
from datetime import datetime
import time
from database.db import db_dependency

class PostagemController:
  async def novo(id, corpo, db: db_dependency):
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
  
  async def lista(quantidade, db: db_dependency):
    try:
      query = select(Postagem, Usuario.nome).join(Usuario, Postagem.usuario_id == Usuario.id).offset(0).limit(quantidade).order_by(Postagem.criado_em.desc())
      response = db.exec(query).all()
      postagens = []  
      for x in response:
        postagens.append({
          "id": x.Postagem.id,
          "usuario": x[1],
          "corpo": x.Postagem.corpo,
          "criado_em": x.Postagem.criado_em.strftime("%d/%m/%Y, %H:%M:%S")
        })
      return JSONResponse(status_code=status.HTTP_200_OK, content=postagens)
    except Exception as e:
      print(e)
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Erro ao listar postagem')