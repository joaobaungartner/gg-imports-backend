from decimal import Decimal

from src.repositories.order_item_repository import OrderItemRepository


class CalculateOrderItemSubtotalUseCase:
    def __init__(self, order_item_repository: OrderItemRepository):
        self.order_item_repository = order_item_repository

    def execute(self, order_item_id: int) -> Decimal:
        item = self.order_item_repository.get_by_id(order_item_id)
        if not item:
            raise ValueError("Item do pedido não encontrado")

        return item.calcular_subtotal()
