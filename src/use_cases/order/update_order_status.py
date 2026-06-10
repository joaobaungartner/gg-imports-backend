from src.entities.order import OrderEntity, OrderStatus
from src.repositories.order_repository import OrderRepository


class UpdateOrderStatusUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
        # TODO: injetar AdminRepository para validar permissão de Admin

    def execute(
        self,
        order_id: int,
        novo_status: str,
        admin_id: int | None = None,
    ) -> OrderEntity:
        # TODO: validar permissão de Admin quando admin_id for informado

        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        try:
            status = OrderStatus(novo_status)
        except ValueError as exc:
            raise ValueError("Status de pedido inválido") from exc

        order.alterar_status(status)

        updated_order = self.order_repository.update_status(
            order_id, order.status.value
        )
        if not updated_order:
            raise ValueError("Pedido não encontrado")

        return updated_order
