from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List


class User(SQLModel, table=True):
    __tablename__ = 'users'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    nome: str = Field(max_length=100)
    email: str = Field(max_length=50)
    senha: str
    saldo_usuario: int = Field(default=0)
    criado_em: datetime = Field(default_factory=datetime.now)
    ativo: bool = Field(default=True)

    password_recovery: List["RecuperaSenha"] = Relationship(
        back_populates="users",
        sa_relationship=relationship("PasswordRecovery", back_populates="users", cascade="all, delete-orphan")
    )

    secret_key: Optional[str] = None
    qrcode: Optional[str] = None
    primeiro_login: bool = Field(default=True)
    refresh_token: Optional[str] = None


class PasswordRecovery(SQLModel, table=True):
    __tablename__ = 'password_recovery'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    usuario_id: int = Field(foreign_key="users.id")
    usuario: Optional[User] = Relationship(back_populates="password_recovery")
    token: str
    criado_em: datetime = Field(default_factory=datetime.now)


