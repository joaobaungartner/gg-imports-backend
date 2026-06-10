from src.entities.order import OrderStatus
from src.entities.order_item import OrderItemEntity
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_repository import OrderRepository


_BLOCKED_STATUSES = {
    OrderStatus.CONFIRMED,
    OrderStatus.PAID,
    OrderStatus.PROCESSING,
    OrderStatus.SHIPPED,
    OrderStatus.DELIVERED,
}


class RemoveOrderItemUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        order_item_repository: OrderItemRepository,
    ):
        self.order_repository = order_repository
        self.order_item_repository = order_item_repository

    def execute(self, order_item_id: int) -> OrderItemEntity:
        item = self.order_item_repository.get_by_id(order_item_id)
        if not item:
            raise ValueError("Item do pedido não encontrado")

        if not item.ativo:
            raise ValueError("Item do pedido não encontrado")

        order = self.order_repository.get_by_id(item.order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        if order.status in _BLOCKED_STATUSES:
            raise ValueError("Pedido não permite alteração de itens")

        deactivated = self.order_item_repository.deactivate(order_item_id)
        if not deactivated:
            raise ValueError("Item do pedido não encontrado")

        from src.use_cases.order.calculate_order_total import (
            CalculateOrderTotalUseCase,
        )

        CalculateOrderTotalUseCase(self.order_repository).execute(item.order_id)

        return deactivated
