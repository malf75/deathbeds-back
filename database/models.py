from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List


class Usuario(SQLModel, table=True):
    __tablename__ = 'usuarios'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    nome: str = Field(max_length=255)
    email: str = Field(max_length=100)
    senha: str
    uf: str = Field(max_length=2)
    cpf: str = Field(max_length=15)
    crm: Optional[str] = Field(max_length=30)
    crp: Optional[str] = Field(max_length=30)
    tipo_usuario_id: int = Field(default=1, foreign_key="tipo_usuario.id")
    profissional_verificado: bool = Field(default=False)
    ativo: bool = Field(default=True)
    secret_key: Optional[str] = None
    qrcode: Optional[str] = None
    primeiro_login: bool = Field(default=True)
    refresh_token: Optional[str] = None
    session_key: Optional[str] = None
    criado_em: datetime = Field(default_factory=datetime.now)
    deletado_em: Optional[datetime] = None

    perfil: List["PerfilUsuario"] = Relationship(back_populates="usuario", cascade_delete=True)
    recupera_senha: List["RecuperaSenha"] = Relationship(back_populates="usuario", cascade_delete=True)
    postagens: List["Postagem"] = Relationship(back_populates="usuario", cascade_delete=True)
    chats_padrao: List["ChatsPadrao"] = Relationship(back_populates="usuario")
    chats_atendimento_profissional: List["ChatsAtendimento"] = Relationship(
        back_populates="profissional",
        sa_relationship_kwargs={"foreign_keys": "[ChatsAtendimento.profissional_id]"},
    )
    chats_atendimento_paciente: List["ChatsAtendimento"] = Relationship(
        back_populates="paciente",
        sa_relationship_kwargs={"foreign_keys": "[ChatsAtendimento.paciente_id]"},
    )
    chats_atendimento_discente: List["ChatsAtendimento"] = Relationship(
        back_populates="discente",
        sa_relationship_kwargs={"foreign_keys": "[ChatsAtendimento.discente_id]"},
    )
    usuarios_chat_padrao: List["UsuariosChatPadrao"] = Relationship(back_populates="usuario")
    mensagens_chat_padrao: List["MensagensChatPadrao"] = Relationship(back_populates="usuario")
    mensagens_chat_atendimento: List["MensagensChatAtendimento"] = Relationship(back_populates="usuario")
    tipo_usuario: Optional["TipoUsuario"] = Relationship(back_populates="usuario")
    seguindo: List["Seguidores"] = Relationship(back_populates="usuario_seguidor", sa_relationship_kwargs={"foreign_keys": "[Seguidores.usuario_seguidor_id]", "cascade": "all, delete-orphan"})
    seguidores: List["Seguidores"] = Relationship(back_populates="usuario_seguido", sa_relationship_kwargs={"foreign_keys": "[Seguidores.usuario_seguido_id]", "cascade": "all, delete-orphan"})
    notificacoes: Optional["Notificacoes"] = Relationship(back_populates="usuario")

class PerfilUsuario(SQLModel, table=True):
    __tablename__ = 'perfil_usuario'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    usuario_id: int = Field(foreign_key="usuarios.id", ondelete="CASCADE")
    usuario: Optional[Usuario] = Relationship(back_populates="perfil")
    bio: Optional[str] = Field(max_length=255)
    foto: Optional[str] = None
    profissao: Optional[str] = Field(max_length=100)
    especializacao: Optional[str] = Field(max_length=100)
    cor: Optional[str] = Field(default="aliceblue")
    privado: bool = Field(default=False)
    deletado_em: Optional[datetime] = None

class TipoUsuario(SQLModel, table=True):
    __tablename__ = 'tipo_usuario'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    descricao: str = Field(max_length=20)

    usuario: List["Usuario"] = Relationship(back_populates="tipo_usuario")

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

class ChatsPadrao(SQLModel, table=True):
    __tablename__ = 'chats_padrao'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    criador_id: int = Field(foreign_key="usuarios.id")
    usuario: Optional[Usuario] = Relationship(back_populates="chats_padrao")
    criado_em: datetime = Field(default_factory=datetime.now)
    deletado_em: Optional[datetime] = None
    nome: str = Field(max_length=50)

    usuarios_chat_padrao: List["UsuariosChatPadrao"] = Relationship(back_populates="chats_padrao")
    mensagens_chat_padrao: List["MensagensChatPadrao"] = Relationship(back_populates="chats_padrao")

class UsuariosChatPadrao(SQLModel, table=True):
    __tablename__ = 'usuarios_chat_padrao'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    chat_id: int = Field(foreign_key="chats_padrao.id")
    chats_padrao: Optional[ChatsPadrao] = Relationship(back_populates="usuarios_chat_padrao")
    usuario_id: int = Field(foreign_key="usuarios.id")
    usuario: Optional[Usuario] = Relationship(back_populates="usuarios_chat_padrao")
    incluido_em: datetime = Field(default_factory=datetime.now)
    excluido_em: Optional[datetime] = None

class MensagensChatPadrao(SQLModel, table=True):
    __tablename__ = 'mensagens_chat_padrao'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    corpo: str = Field(max_length=1000)
    chat_id: int = Field(foreign_key="chats_padrao.id")
    chats_padrao: Optional[ChatsPadrao] = Relationship(back_populates="mensagens_chat_padrao")
    usuario_id: int = Field(foreign_key="usuarios.id")
    usuario: Optional[Usuario] = Relationship(back_populates="mensagens_chat_padrao")
    criado_em: datetime = Field(default_factory=datetime.now)
    deletado_em: Optional[datetime] = None

class ChatsAtendimento(SQLModel, table=True):
    __tablename__ = 'chats_atendimento'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    profissional_id: int = Field(foreign_key="usuarios.id")
    profissional: Optional[Usuario] = Relationship(
        back_populates="chats_atendimento_profissional",
        sa_relationship_kwargs={"foreign_keys": "[ChatsAtendimento.profissional_id]"},
    )
    paciente_id: int = Field(foreign_key="usuarios.id")
    paciente: Optional[Usuario] = Relationship(
        back_populates="chats_atendimento_paciente",
        sa_relationship_kwargs={"foreign_keys": "[ChatsAtendimento.paciente_id]"},
    )
    discente_id: Optional[int] = Field(foreign_key="usuarios.id")
    discente: Optional[Usuario] = Relationship(
        back_populates="chats_atendimento_discente",
        sa_relationship_kwargs={"foreign_keys": "[ChatsAtendimento.discente_id]"},
    )
    horario_inicio: Optional[datetime] = None
    horario_final: Optional[datetime] = None
    criado_em: datetime = Field(default_factory=datetime.now)
    deletado_em: Optional[datetime] = None

    mensagens_chat_atendimento: List["MensagensChatAtendimento"] = Relationship(back_populates="chats_atendimento")

class MensagensChatAtendimento(SQLModel, table=True):
    __tablename__ = 'mensagens_chat_atendimento'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    corpo: str = Field(max_length=1000)
    chat_id: int = Field(foreign_key="chats_atendimento.id")
    chats_atendimento: Optional[ChatsAtendimento] = Relationship(back_populates="mensagens_chat_atendimento")
    usuario_id: int = Field(foreign_key="usuarios.id")
    usuario: Optional[Usuario] = Relationship(back_populates="mensagens_chat_atendimento")
    criado_em: datetime = Field(default_factory=datetime.now)
    deletado_em: Optional[datetime] = None

class Seguidores(SQLModel, table=True):
    __tablename__ = 'seguidores'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    usuario_seguidor_id: int = Field(foreign_key="usuarios.id")
    usuario_seguidor: Optional[Usuario] = Relationship(back_populates="seguindo", sa_relationship_kwargs={"foreign_keys": "[Seguidores.usuario_seguidor_id]"})
    usuario_seguido_id: int = Field(foreign_key="usuarios.id")
    usuario_seguido: Optional[Usuario] = Relationship(back_populates="seguidores", sa_relationship_kwargs={"foreign_keys": "[Seguidores.usuario_seguido_id]"})

class Notificacoes(SQLModel, table=True):
    __tablename__ = 'notificacoes'

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    usuario_id: int = Field(foreign_key="usuarios.id")
    usuario: Optional[Usuario] = Relationship(back_populates="notificacoes")
    corpo: str = Field(max_length=255)
    lido: bool = Field(default=False)
    criado_em: datetime = Field(default=datetime.now)