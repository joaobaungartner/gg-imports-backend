from src.entities.order import OrderEntity
from src.repositories.order_repository import OrderRepository


class CancelOrderUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def execute(self, order_id: int) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        order.cancelar_pedido()

        # TODO: integrar com PaymentRepository para estorno, se pagamento existir
        # TODO: integrar com ProductRepository para devolver estoque, se já houve baixa

        updated_order = self.order_repository.update_status(
            order_id, order.status.value
        )
        if not updated_order:
            raise ValueError("Pedido não encontrado")

        return updated_order
