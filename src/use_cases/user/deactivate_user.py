from src.entities.user import UserEntity
from src.repositories.user_repository import UserRepository


class DeactivateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, user_id: int) -> UserEntity:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")

        deactivated_user = self.user_repository.deactivate(user_id)
        if not deactivated_user:
            raise ValueError("Usuário não encontrado")

        return deactivated_user
