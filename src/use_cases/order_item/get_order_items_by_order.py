from src.entities.order_item import OrderItemEntity
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_repository import OrderRepository


class GetOrderItemsByOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        order_item_repository: OrderItemRepository,
    ):
        self.order_repository = order_repository
        self.order_item_repository = order_item_repository

    def execute(self, order_id: int) -> list[OrderItemEntity]:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        return self.order_item_repository.get_by_order_id(order_id)
