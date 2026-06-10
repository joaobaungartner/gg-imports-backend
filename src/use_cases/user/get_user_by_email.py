from src.entities.user import UserEntity
from src.repositories.user_repository import UserRepository


class GetUserByEmailUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, email: str) -> UserEntity:
        user = self.user_repository.get_by_email(email)
        if not user:
            raise ValueError("Usuário não encontrado")
        return user
