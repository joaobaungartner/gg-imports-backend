from src.entities.client import ClientEntity
from src.repositories.client_repository import ClientRepository
from src.repositories.user_repository import UserRepository


class DeactivateClientUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        client_repository: ClientRepository,
    ):
        self.user_repository = user_repository
        self.client_repository = client_repository

    def execute(self, client_id: int) -> ClientEntity:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")

        deactivated_client = self.client_repository.deactivate(client_id)
        if not deactivated_client:
            raise ValueError("Cliente não encontrado")

        deactivated_user = self.user_repository.deactivate(client.id)
        if not deactivated_user:
            raise ValueError("Usuário não encontrado")

        return self.client_repository.get_by_id(client_id)
