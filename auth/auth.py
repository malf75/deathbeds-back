import re
import secrets
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, File
from fastapi.responses import JSONResponse
from sqlmodel import select
from starlette import status
from database.db import db_dependency
from database.models import Usuario, RecuperaSenha
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from setup.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_TIME, REFRESH_TOKEN_EXPIRE_TIME, APP_URL, email_conf
from pydantic import BaseModel, EmailStr
from auth.m2f import *
from email_validator import validate_email
from password_validator import PasswordValidator
from typing import Optional

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/login')

class TokenRequest(BaseModel):
    token: str

schema = PasswordValidator()
schema.min(8).max(100).has().uppercase().has().lowercase().has().digits().has().symbols().has().no().spaces()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,
                    nome: str = Form(...),
                    email: EmailStr = Form(...),
                    cpf: str = Form(...),
                    crm_crp: Optional[str] = Form(None),
                    password: str = Form(...),
                    tipo_usuario: int = Form(...),
                    foto: Optional[UploadFile] = File(None),
                    uf: str = Form(...),
                    tipo: str = Form(...)
                    ):
    try:
        emailinfo = validate_email(email, check_deliverability=True)
        emailnormalized = emailinfo.normalized
        if nome == '':
            raise Exception("O campo de nome deve ser preenchido")
        if password == '':
            raise Exception("O campo de senha deve ser preenchido")
        if not schema.validate(password):
            raise Exception("Esta senha não é válida")
        if not emailnormalized:
            raise Exception("Este email não é válido")
        secret_encoded, qrcode = gera_m2f(email)
        if tipo_usuario == 1:
            create_user_model = Usuario(
                nome=nome,
                email=email,
                uf=uf,
                cpf=cpf,
                senha=bcrypt_context.hash(password),
                secret_key=secret_encoded,
                qrcode=qrcode
            )
        if tipo_usuario == 2:
            if tipo == "CRP":
                create_user_model = Usuario(
                    nome=nome,
                    email=email,
                    uf=uf,
                    cpf=cpf,
                    crp=crm_crp,
                    senha=bcrypt_context.hash(password),
                    secret_key=secret_encoded,
                    qrcode=qrcode
                )
            if tipo == "CRM":
                create_user_model = Usuario(
                    nome=nome,
                    email=email,
                    uf=uf,
                    cpf=cpf,
                    crm=crm_crp,
                    senha=bcrypt_context.hash(password),
                    secret_key=secret_encoded,
                    qrcode=qrcode
                )
        query = select(Usuario).where(Usuario.email == create_user_model.email)
        consulta = db.exec(query).first()
        if consulta:
            raise Exception("Email já existente")
        else:
            db.add(create_user_model)
            db.commit()
            return JSONResponse(status_code=status.HTTP_201_CREATED, content="Usuário criado com sucesso")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{e}")

@router.post("/login")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    try:
        try:
            user = authenticate_user(form_data.username, form_data.password, db)
        except Exception as e:
            raise Exception(e)
        if user.primeiro_login == True:
            key = secrets.token_hex(16)
            query = select(Usuario).where(Usuario.email == form_data.username)
            usuario = db.exec(query).first()
            usuario.session_key = key
            db.commit()
            return JSONResponse(status_code=status.HTTP_200_OK, content={"id":user.id, "key": key})
        return JSONResponse(status_code=status.HTTP_200_OK, content={"id":user.id,"primeiro_login":user.primeiro_login})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Erro ao realizar login: {e}")

@router.get("/qr/{id}/{key}")
async def qrcode(id: int, key: str, db: db_dependency):
    try:
        statement = select(Usuario).where(Usuario.id == id)
        query = db.exec(statement).first()
        if query.session_key == key:
            query.session_key = None
            db.commit()
            return JSONResponse(status_code=status.HTTP_200_OK, content={"qrcode": query.qrcode, "id":f"{id}"})
        else:
            raise Exception("Erro a retornar qrcode")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao requisitar qrcode: {e}")

@router.post("/m2f/{id}")
async def m2f_verification(id: int, otp: str, db: db_dependency):
    statement = select(Usuario).where(Usuario.id == id)
    query = db.exec(statement).first()
    verify = verifica_m2f(query.secret_key, otp)
    if verify == True:
        query.primeiro_login = False
        query.qrcode = ''
        tokens = create_access_token(query.email, query.id, db)
        db.commit()
        return JSONResponse(status_code=status.HTTP_200_OK, content={"tokens": tokens})
    else:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="OTP inválido")
    
@router.get("/m2f/recovery/{id}")
async def m2f_recovery(id: int, db: db_dependency):
    try:
       statement = select(Usuario).where(Usuario.id == id)
       query = db.exec(statement).first()
       return await recupera_m2f(query.email, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao recuperar m2f: {e}")

def authenticate_user(email: str, password: str, db):
    try:
        user = select(Usuario).where(Usuario.email == email)
        query = db.exec(user).first()
        if not query:
            raise Exception("Usuário não registrado")
        if not bcrypt_context.verify(password, query.senha):
            raise Exception("Senha incorreta")
        return query
    except Exception as e:
        raise e

def create_access_token(email: str, user_id: int, db: db_dependency):
    try:
        access_encode = {"sub": email, "id": user_id}
        access_expires = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_TIME)
        access_encode.update({"exp": access_expires})
        refresh_encode = {"sub": email, "id": user_id}
        refresh_expires = datetime.now(timezone.utc) + timedelta(hours=REFRESH_TOKEN_EXPIRE_TIME)
        refresh_encode.update({"exp": refresh_expires})
        access_jwt = jwt.encode(access_encode, SECRET_KEY, algorithm=ALGORITHM)
        refresh_jwt = jwt.encode(refresh_encode, SECRET_KEY, algorithm=ALGORITHM)
        user = select(Usuario).where(Usuario.id == user_id)
        query = db.exec(user).first()
        query.refresh_token = refresh_jwt
        db.commit()
        return [{"access_token": access_jwt, "token_type": "Bearer", "expires_in": f"{ACCESS_TOKEN_EXPIRE_TIME} Hours"},{"refresh_token": refresh_jwt, "token_type": "Bearer", "expires_in": f"{REFRESH_TOKEN_EXPIRE_TIME} Hours"}]
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Erro ao gerar token o usuário:{e}")
    
@router.get("/user")
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        if email is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Não pode verificar o usuário.")
        query = select(Usuario).where(Usuario.id == user_id)
        user = db.exec(query).first()
        return {"email": email, "id": user_id, "nome": user.nome}
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Erro ao verificar o usuário:{e}")

@router.post("/token/refresh")
async def refresh_token(token_request: TokenRequest, db: db_dependency):
    try:
        refresh = jwt.decode(token_request.token, SECRET_KEY, algorithms=[ALGORITHM])
        id = refresh.get("id")
        user = select(Usuario).where(Usuario.id == id)
        query = db.exec(user).first()
        exp_timestamp = refresh.get("exp")
        if query.refresh_token == token_request.token:
            exp_datetime = datetime.fromtimestamp(exp_timestamp, timezone.utc)
            if datetime.now(timezone.utc) > exp_datetime:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Refresh token expirou, refaça o login.")
            else:
                token = create_access_token(query.email, query.id, db)
                db.commit()
                return token
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Refresh token inválido, refaça o login.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Ocorreu um erro ao verificar o token: {e} token: {refresh_token}")


@router.post("/recuperasenha")
async def token_recupera_senha(email: EmailStr, db: db_dependency):
    try:
        user = select(Usuario).where(Usuario.email == email)
        query = db.exec(user).first()
        token = re.sub(r'[./\\]','',bcrypt_context.hash(email))
        cria_token = RecuperaSenha(
            usuario_id = query.id,
            token = token
        )
        db.add(cria_token)
        db.commit()
        try:
            body = templates.get_template('email.html').render(url=str(f"{APP_URL}/recover?token={token}"), title="Recuperação de senha", message="Seu link de recuperação de senha foi gerado:")
            message = MessageSchema(
                subject="Recuperação de Senha",
                recipients=[email],
                body=body,
                subtype='html',
                headers={"Content-Type": "text/html; charset=UTF-8"}
            )
            fm = FastMail(email_conf)
            await fm.send_message(message)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")
        return {"message":"Email de Recuperação Enviado"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Erro ao gerar email de recuperação: {e}")
    
@router.post("/recuperasenha/{token}")
async def recupera_senha(token: str, nova_senha: str, db: db_dependency):
    try:
        query = select(RecuperaSenha).where(RecuperaSenha.token == token)
        result = db.exec(query).first()
        if not result:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token Inválido")
        else:
            user = select(Usuario).where(Usuario.id == result.usuario_id)
            query = db.exec(user).first()
            query.senha = bcrypt_context.hash(nova_senha)
            db.delete(result)
            db.commit()
            return {"message":"Senha Alterada"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro ao recuperar senha: {e}")
