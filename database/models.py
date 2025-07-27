from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List


class Usuario(SQLModel, table=True):
    __tablename__ = 'usuarios'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    nome: str = Field(max_length=100)
    email: str = Field(max_length=50)
    senha: str
    ativo: bool = Field(default=True)
    secret_key: Optional[str] = None
    qrcode: Optional[str] = None
    primeiro_login: bool = Field(default=True)
    refresh_token: Optional[str] = None
    session_key: Optional[str] = None
    criado_em: datetime = Field(default_factory=datetime.now)
    deletado_em: Optional[datetime] = None

    recupera_senha: List["RecuperaSenha"] = Relationship(back_populates="usuario", cascade_delete=True)
    postagens: List["Postagem"] = Relationship(back_populates="usuario", cascade_delete=True)


class RecuperaSenha(SQLModel, table=True):
    __tablename__ = 'recupera_senha'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    usuario_id: int = Field(foreign_key="usuarios.id", ondelete="CASCADE")
    usuario: Optional[Usuario] = Relationship(back_populates="recupera_senha")
    token: str
    criado_em: datetime = Field(default_factory=datetime.now)

class Postagem(SQLModel, table=True):
    __tablename__ = 'postagens'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    corpo: str = Field(max_length=255)
    usuario_id: int = Field(foreign_key="usuarios.id", ondelete="CASCADE")
    usuario: Optional[Usuario] = Relationship(back_populates="postagens")
    criado_em: datetime = Field(default_factory=datetime.now)
    deletado_em: Optional[datetime] = None
