from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminCreate(BaseModel):
    nome: str = Field(..., min_length=1)
    email: EmailStr
    senha: str = Field(..., min_length=1)
    telefone: str | None = None


class AdminUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1)
    telefone: str | None = None
    email: EmailStr | None = None


class AdminResponse(BaseModel):
    id: int
    user_id: int
    nome: str
    email: str
    telefone: str | None = None
    role: str
    ativo: bool
    data_cadastro: datetime

    class Config:
        from_attributes = True
