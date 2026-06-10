from src.entities.address import AddressEntity
from src.repositories.address_repository import AddressRepository


class ListAddressesUseCase:
    def __init__(self, address_repository: AddressRepository):
        self.address_repository = address_repository

    def execute(self, ativo: bool | None = None) -> list[AddressEntity]:
        if ativo is True:
            return self.address_repository.list_active()
        if ativo is False:
            return [
                address
                for address in self.address_repository.list_all()
                if not address.ativo
            ]
        return self.address_repository.list_all()
