from src.entities.order import OrderEntity, OrderStatus
from src.repositories.order_repository import OrderRepository


class RemoveOrderItemUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def execute(self, order_id: int, item_id: int) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        if order.status == OrderStatus.CONFIRMED and len(order.itens) <= 1:
            raise ValueError("Pedido sem itens")

        order.remover_item(item_id)

        updated_order = self.order_repository.remove_item(order_id, item_id)
        if not updated_order:
            raise ValueError("Pedido não encontrado")

        order.calcular_total()
        final_order = self.order_repository.update(
            order_id, {"valor_total": order.valor_total}
        )
        if not final_order:
            raise ValueError("Pedido não encontrado")

        return final_order
