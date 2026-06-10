from src.entities.address import AddressEntity
from src.repositories.address_repository import AddressRepository


class UpdateAddressUseCase:
    def __init__(self, address_repository: AddressRepository):
        self.address_repository = address_repository

    def execute(
        self,
        address_id: int,
        rua: str | None = None,
        numero: str | None = None,
        bairro: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        cep: str | None = None,
    ) -> AddressEntity:
        address = self.address_repository.get_by_id(address_id)
        if not address:
            raise ValueError("Endereço não encontrado")

        address.atualizar_endereco(
            rua=rua,
            numero=numero,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
            cep=cep,
        )

        update_data = {}
        if rua is not None:
            update_data["rua"] = address.rua
        if numero is not None:
            update_data["numero"] = address.numero
        if bairro is not None:
            update_data["bairro"] = address.bairro
        if cidade is not None:
            update_data["cidade"] = address.cidade
        if estado is not None:
            update_data["estado"] = address.estado
        if cep is not None:
            update_data["cep"] = address.cep

        if not update_data:
            return address

        updated_address = self.address_repository.update(address_id, update_data)
        if not updated_address:
            raise ValueError("Endereço não encontrado")

        return updated_address
