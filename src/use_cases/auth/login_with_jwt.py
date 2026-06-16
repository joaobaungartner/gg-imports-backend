from dataclasses import dataclass

from src.config.config import get_settings
from src.entities.user import UserEntity
from src.use_cases.user.authenticate_user import AuthenticateUserUseCase
from src.utils.jwt import create_access_token


@dataclass
class LoginWithJwtResult:
    access_token: str
    token_type: str
    expires_in: int
    user: UserEntity


class LoginWithJwtUseCase:
    def __init__(self, authenticate_user_use_case: AuthenticateUserUseCase):
        self.authenticate_user_use_case = authenticate_user_use_case

    def execute(self, email: str, senha: str) -> LoginWithJwtResult:
        user = self.authenticate_user_use_case.execute(email, senha)

        role = user.role.value if hasattr(user.role, "value") else str(user.role)
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": role,
        }

        try:
            access_token = create_access_token(token_data)
        except Exception as exc:
            raise ValueError("Erro ao gerar token") from exc

        settings = get_settings()
        return LoginWithJwtResult(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=user,
        )
