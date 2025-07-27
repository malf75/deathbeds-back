from pydantic import BaseModel

class CriaPostagemRequest(BaseModel):
    id: int
    corpo: str