from src.entities.address import AddressEntity
from src.repositories.address_repository import AddressRepository


class ValidateAddressForOrderUseCase:
    def __init__(self, address_repository: AddressRepository):
        self.address_repository = address_repository

    def execute(self, address_id: int, client_id: int) -> AddressEntity:
        address = self.address_repository.get_by_id(address_id)
        if not address:
            raise ValueError("Endereço não encontrado")

        if not address.ativo:
            raise ValueError("Endereço inativo")

        if not self.address_repository.address_belongs_to_client(
            address_id, client_id
        ):
            raise ValueError("Endereço não pertence ao cliente")

        address.validar_endereco()
        return address
