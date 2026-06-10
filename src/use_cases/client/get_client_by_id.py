from src.entities.client import ClientEntity
from src.repositories.client_repository import ClientRepository


class GetClientByIdUseCase:
    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    def execute(self, client_id: int) -> ClientEntity:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        return client
