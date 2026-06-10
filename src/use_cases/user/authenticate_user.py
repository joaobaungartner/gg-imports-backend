from src.entities.user import UserEntity
from src.repositories.user_repository import UserRepository
from src.utils.password import verify_password


class AuthenticateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, email: str, senha: str) -> UserEntity:
        user = self.user_repository.get_by_email(email)
        if not user:
            raise ValueError("Credenciais inválidas")

        if not user.ativo:
            raise ValueError("Usuário inativo")

        if not verify_password(senha, user.senha_hash):
            raise ValueError("Credenciais inválidas")

        return user
