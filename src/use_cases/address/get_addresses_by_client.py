from src.entities.address import AddressEntity
from src.repositories.address_repository import AddressRepository
from src.repositories.client_repository import ClientRepository


class GetAddressesByClientUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        address_repository: AddressRepository,
    ):
        self.client_repository = client_repository
        self.address_repository = address_repository

    def execute(self, client_id: int) -> list[AddressEntity]:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        return self.address_repository.get_by_client_id(client_id)
