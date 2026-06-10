from src.entities.user import UserEntity
from src.repositories.user_repository import UserRepository


class UpdateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(
        self,
        user_id: int,
        nome: str | None = None,
        telefone: str | None = None,
    ) -> UserEntity:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")

        user.atualizar_perfil(nome=nome, telefone=telefone)

        update_data = {}
        if nome is not None:
            update_data["nome"] = user.nome
        if telefone is not None:
            update_data["telefone"] = user.telefone

        updated_user = self.user_repository.update(user_id, update_data)
        if not updated_user:
            raise ValueError("Usuário não encontrado")

        return updated_user
