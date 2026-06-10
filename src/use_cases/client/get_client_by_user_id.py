from src.entities.client import ClientEntity
from src.repositories.client_repository import ClientRepository


class GetClientByUserIdUseCase:
    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    def execute(self, user_id: int) -> ClientEntity:
        client = self.client_repository.get_by_user_id(user_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        return client
