from src.entities.order import OrderEntity
from src.repositories.client_repository import ClientRepository
from src.repositories.order_repository import OrderRepository


class GetMyOrdersUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        order_repository: OrderRepository,
    ):
        self.client_repository = client_repository
        self.order_repository = order_repository

    def execute(self, user_id: int) -> list[OrderEntity]:
        client = self.client_repository.get_by_user_id(user_id)
        if not client:
            return []

        orders = self.order_repository.get_by_client_id(client.client_id)
        return sorted(
            orders,
            key=lambda order: order.data_pedido or "",
            reverse=True,
        )
