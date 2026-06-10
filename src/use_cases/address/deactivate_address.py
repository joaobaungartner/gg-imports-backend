from src.entities.address import AddressEntity
from src.repositories.address_repository import AddressRepository


class DeactivateAddressUseCase:
    def __init__(self, address_repository: AddressRepository):
        self.address_repository = address_repository

    def execute(self, address_id: int) -> AddressEntity:
        address = self.address_repository.get_by_id(address_id)
        if not address:
            raise ValueError("Endereço não encontrado")

        address.desativar()

        deactivated_address = self.address_repository.deactivate(address_id)
        if not deactivated_address:
            raise ValueError("Endereço não encontrado")

        return deactivated_address
