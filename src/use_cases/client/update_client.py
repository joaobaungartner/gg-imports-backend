import re

from src.entities.client import ClientEntity
from src.repositories.client_repository import ClientRepository
from src.repositories.user_repository import UserRepository


class UpdateClientUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        client_repository: ClientRepository,
    ):
        self.user_repository = user_repository
        self.client_repository = client_repository

    def execute(
        self,
        client_id: int,
        nome: str | None = None,
        telefone: str | None = None,
        cpf: str | None = None,
    ) -> ClientEntity:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")

        client.atualizar_perfil(nome=nome, telefone=telefone)

        user_update_data = {}
        if nome is not None:
            user_update_data["nome"] = client.nome
        if telefone is not None:
            user_update_data["telefone"] = client.telefone

        if user_update_data:
            updated_user = self.user_repository.update(client.id, user_update_data)
            if not updated_user:
                raise ValueError("Usuário não encontrado")

        client_update_data = {}
        if cpf is not None:
            cpf_digits = re.sub(r"\D", "", cpf)
            if cpf_digits != client.cpf and self.client_repository.cpf_exists(
                cpf_digits
            ):
                raise ValueError("CPF já cadastrado")
            client.cpf = cpf_digits
            client._validate_cpf()
            client_update_data["cpf"] = client.cpf

        if client_update_data:
            updated_client = self.client_repository.update(
                client_id, client_update_data
            )
            if not updated_client:
                raise ValueError("Cliente não encontrado")
            return updated_client

        return self.client_repository.get_by_id(client_id)
