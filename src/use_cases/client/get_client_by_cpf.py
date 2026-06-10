import re

from src.entities.client import ClientEntity
from src.repositories.client_repository import ClientRepository


class GetClientByCpfUseCase:
    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    def execute(self, cpf: str) -> ClientEntity:
        cpf_digits = re.sub(r"\D", "", cpf)
        client = self.client_repository.get_by_cpf(cpf_digits)
        if not client:
            raise ValueError("Cliente não encontrado")
        return client
