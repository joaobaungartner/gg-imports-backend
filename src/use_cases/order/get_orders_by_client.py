from src.entities.order import OrderEntity
from src.repositories.client_repository import ClientRepository
from src.repositories.order_repository import OrderRepository


class GetOrdersByClientUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        order_repository: OrderRepository,
    ):
        self.client_repository = client_repository
        self.order_repository = order_repository

    def execute(self, client_id: int) -> list[OrderEntity]:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        return self.order_repository.get_by_client_id(client_id)
