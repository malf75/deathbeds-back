from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from database.db import db_dependency
from sqlmodel import select
from sqlalchemy.orm import aliased
from sqlalchemy import or_, func
from starlette import status
from pydantic import BaseModel
from database.models import Usuario, ChatsPadrao, UsuariosChatPadrao, MensagensChatPadrao

class ChatController:
    async def novo(usuario_id, destinatarios_id, nome, db: db_dependency):
        try:
            igualdade = False
            primeiro_chat = True
            query = select(ChatsPadrao).where(ChatsPadrao.criador_id == usuario_id)
            chats = db.exec(query).all()
            if len(chats) > 0:
                primeiro_chat = False
            if not primeiro_chat:
                for chat in chats:
                    query = select(UsuariosChatPadrao).where(UsuariosChatPadrao.chat_id == chat.id)
                    chat_encontrado = db.exec(query).all()
                    ids_participantes = [p.usuario_id for p in chat_encontrado]
                    if set(ids_participantes) == set(destinatarios_id):
                        igualdade = True
                        raise Exception("Chat já existente")
            if not igualdade or primeiro_chat:
                if nome:
                    chat = ChatsPadrao(
                            criador_id=usuario_id,
                            nome=nome
                        )
                    db.add(chat)
                else:
                    chat = ChatsPadrao(
                            criador_id=usuario_id,
                            nome="temp"
                        )                    
                    db.add(chat)
                    db.flush()
                    chat.nome = f"chat_{chat.id}"
                db.flush()
                for id in destinatarios_id:
                    usuario = UsuariosChatPadrao(
                            chat_id=chat.id,
                            usuario_id=id,
                        )
                    db.add(usuario)
                    db.commit() 
            return JSONResponse(status_code=status.HTTP_201_CREATED, content="Chat criado com sucesso")
        except Exception as e:
            print(e)    
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar chat: {e}")
    
    async def lista(usuario_id, quantidade, db: db_dependency):
        try:
            UsuarioCriador = aliased(Usuario)
            UsuarioParticipante = aliased(Usuario)
            query = (select(ChatsPadrao, 
                           UsuariosChatPadrao, 
                           UsuarioCriador.id.label("criador_id"), 
                           UsuarioCriador.nome.label("criador_nome"), 
                           UsuarioParticipante.id.label("participante_id"), 
                           UsuarioParticipante.nome.label("participante_nome"))
            .join(UsuariosChatPadrao, UsuariosChatPadrao.chat_id == ChatsPadrao.id)
            .join(UsuarioCriador, ChatsPadrao.criador_id == UsuarioCriador.id)
            .join(UsuarioParticipante, UsuariosChatPadrao.usuario_id == UsuarioParticipante.id)
            .where(or_(UsuariosChatPadrao.usuario_id == usuario_id, ChatsPadrao.criador_id == usuario_id))
            .offset(0)
            .limit(quantidade)
            )
            chats = db.exec(query).all()
            lista_chat = {}
            for chat in chats:
                if chat.ChatsPadrao.id not in lista_chat:
                    lista_chat[chat.ChatsPadrao.id] = {
                        "id": chat.ChatsPadrao.id,
                        "nome": chat.ChatsPadrao.nome,
                        "criador_id": chat.criador_id,
                        "criador": chat.criador_nome,
                        "participantes": [],
                        "criado_em": chat.ChatsPadrao.criado_em.strftime("%d/%m/%Y, %H:%M:%S")
                    }
                participante = {
                    "id": chat.participante_id,
                    "nome": chat.participante_nome
                }

                if not any(p["id"] == participante["id"] for p in lista_chat[chat.ChatsPadrao.id]["participantes"]):
                    lista_chat[chat.ChatsPadrao.id]["participantes"].append(participante)
                
            return JSONResponse(status_code=status.HTTP_200_OK, content=list(lista_chat.values()))
        except Exception as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao listar chats: {e}")
        
    async def retorna_chat(usuario_id, chat_id, quantidade, db: db_dependency):
        try:
            UsuarioCriador = aliased(Usuario)
            UsuarioParticipante = aliased(Usuario)

            query_chat = (
                select(
                    ChatsPadrao,
                    UsuarioCriador.id.label("criador_id"),
                    UsuarioCriador.nome.label("criador_nome"),
                    UsuarioParticipante.id.label("participante_id"),
                    UsuarioParticipante.nome.label("participante_nome"),
                )
                .join(UsuariosChatPadrao, UsuariosChatPadrao.chat_id == ChatsPadrao.id)
                .join(UsuarioCriador, ChatsPadrao.criador_id == UsuarioCriador.id)
                .join(UsuarioParticipante, UsuariosChatPadrao.usuario_id == UsuarioParticipante.id)
                .where(
                    or_(
                        UsuariosChatPadrao.usuario_id == usuario_id,
                        ChatsPadrao.criador_id == usuario_id,
                    )
                )
                .where(ChatsPadrao.id == chat_id)
            )

            chat_rows = db.exec(query_chat).all()
            if not chat_rows:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat não encontrado ou usuário não tem acesso.",
                )

            chat_base = chat_rows[0]
            lista_chat = {
                "id": chat_base.ChatsPadrao.id,
                "nome": chat_base.ChatsPadrao.nome,
                "criador_id": chat_base.criador_id,
                "criador": chat_base.criador_nome,
                "participantes": [],
                "mensagens": [],
                "criado_em": chat_base.ChatsPadrao.criado_em.strftime("%d/%m/%Y, %H:%M:%S"),
            }

            for row in chat_rows:
                participante = {
                    "id": row.participante_id,
                    "nome": row.participante_nome,
                }
                if not any(p["id"] == participante["id"] for p in lista_chat["participantes"]):
                    lista_chat["participantes"].append(participante)

            total_mensagens = db.exec(
                select(func.count(MensagensChatPadrao.id)).where(MensagensChatPadrao.chat_id == chat_id)
            ).one()

            offset = max(total_mensagens - quantidade, 0)

            query_msgs = (
                select(MensagensChatPadrao)
                .where(MensagensChatPadrao.chat_id == chat_id)
                .order_by(MensagensChatPadrao.criado_em.asc())
                .limit(quantidade)
                .offset(offset)
            )

            mensagens = db.exec(query_msgs).all()

            lista_chat["mensagens"] = [
                {
                    "id": msg.id,
                    "corpo": msg.corpo,
                    "chat_id": msg.chat_id,
                    "usuario_id": msg.usuario_id,
                    "criado_em": msg.criado_em.strftime("%d/%m/%Y, %H:%M:%S"),
                }
                for msg in mensagens
            ]

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=lista_chat,
            )

        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao listar chats",
            )
        
    async def cria_mensagem(usuario_id, chat_id, corpo, db: db_dependency):
        try:
            query = select(ChatsPadrao).where(ChatsPadrao.id == chat_id).where(ChatsPadrao.criador_id == usuario_id)
            chat = db.exec(query).first()
            query = select(UsuariosChatPadrao).where(UsuariosChatPadrao.chat_id == chat_id).where(UsuariosChatPadrao.usuario_id == usuario_id)
            participante = db.exec(query).first()
            if chat or participante:
                mensagem = MensagensChatPadrao(
                    corpo=corpo,
                    usuario_id=usuario_id,
                    chat_id=chat_id
                )
                db.add(mensagem)
                db.commit()
                return mensagem
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao criar mensagem"
            )

    async def retorna_usuarios_participantes(chat_id, db: db_dependency):
        try:
            query = select(UsuariosChatPadrao.usuario_id).where(UsuariosChatPadrao.chat_id == chat_id)
            participantes = db.exec(query).all()
            query = select(ChatsPadrao.criador_id).where(ChatsPadrao.id == chat_id)
            criador = db.exec(query).first()
            lista_participantes = []
            lista_participantes.append(criador)
            for p in participantes:
                lista_participantes.append(p)
            return lista_participantes
        except Exception as e:
            print(e)