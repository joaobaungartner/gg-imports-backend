from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ClientCreate(BaseModel):
    nome: str = Field(..., min_length=1)
    email: EmailStr
    senha: str = Field(..., min_length=1)
    telefone: str | None = None
    cpf: str


class ClientUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1)
    telefone: str | None = None
    cpf: str | None = None


class ClientResponse(BaseModel):
    id: int
    user_id: int
    nome: str
    email: str
    telefone: str | None = None
    cpf: str
    role: str
    ativo: bool
    data_cadastro: datetime

    class Config:
        from_attributes = True


class ClientCartAdd(BaseModel):
    produto_id: int = Field(..., gt=0)
    quantidade: int = Field(..., gt=0)
