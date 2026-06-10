from src.entities.address import AddressEntity
from src.repositories.address_repository import AddressRepository


class GetAddressByIdUseCase:
    def __init__(self, address_repository: AddressRepository):
        self.address_repository = address_repository

    def execute(self, address_id: int) -> AddressEntity:
        address = self.address_repository.get_by_id(address_id)
        if not address:
            raise ValueError("Endereço não encontrado")
        return address
