from src.entities.client import ClientEntity
from src.repositories.client_repository import ClientRepository


class ListClientOrdersUseCase:
    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository
        # TODO: injetar OrderRepository quando disponível

    def execute(self, client_id: int) -> list:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")

        client.visualizar_pedidos()

        # TODO: integrar com OrderRepository para buscar pedidos do cliente
        # Exemplo futuro:
        # return self.order_repository.list_by_client_id(client_id)
        return []
