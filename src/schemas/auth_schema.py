from datetime import datetime

from pydantic import BaseModel

from src.schemas.address_schema import AddressListResponse
from src.schemas.user_schema import UserResponse


class AuthLogin(BaseModel):
    email: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class AuthMeResponse(BaseModel):
    id: int
    nome: str
    email: str
    telefone: str | None = None
    role: str
    ativo: bool
    data_cadastro: datetime
    client_id: int | None = None
    cpf: str | None = None
    endereco: AddressListResponse | None = None
