from pydantic import BaseModel
from typing import Optional

class CriaChatRequest(BaseModel):
    usuario_id: int
    destinatarios_id: list
    nome: Optional[str]