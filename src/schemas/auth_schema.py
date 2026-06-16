from pydantic import BaseModel

from src.schemas.user_schema import UserResponse


class AuthLogin(BaseModel):
    email: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse
