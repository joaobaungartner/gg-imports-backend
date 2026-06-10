from src.entities.order import OrderEntity
from src.repositories.order_repository import OrderRepository


class GetOrderByIdUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def execute(self, order_id: int) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")
        return order
