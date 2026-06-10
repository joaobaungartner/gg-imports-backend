from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    nome: str = Field(..., min_length=1)
    email: str
    senha: str = Field(..., min_length=1)
    telefone: str | None = None
    role: str = "CLIENTE"


class UserUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1)
    telefone: str | None = None


class UserResponse(BaseModel):
    id: int
    nome: str
    email: str
    telefone: str | None = None
    data_cadastro: datetime
    role: str
    ativo: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: str
    senha: str
