from src.entities.address import AddressEntity
from src.repositories.address_repository import AddressRepository
from src.repositories.client_repository import ClientRepository


class CreateAddressUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        address_repository: AddressRepository,
    ):
        self.client_repository = client_repository
        self.address_repository = address_repository

    def execute(
        self,
        client_id: int,
        rua: str,
        numero: str,
        bairro: str,
        cidade: str,
        estado: str,
        cep: str,
    ) -> AddressEntity:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        if not client.ativo:
            raise ValueError("Cliente inativo")

        address = AddressEntity(
            id=None,
            client_id=client_id,
            rua=rua,
            numero=numero,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
            cep=cep,
        )

        return self.address_repository.create(address)
