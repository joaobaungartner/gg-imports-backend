from src.entities.order import OrderEntity
from src.repositories.order_repository import OrderRepository
from src.repositories.order_status_history_repository import (
    OrderStatusHistoryRepository,
)


class GetAdminOrderByIdUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        history_repository: OrderStatusHistoryRepository,
    ):
        self.order_repository = order_repository
        self.history_repository = history_repository

    def execute(self, order_id: int) -> tuple[OrderEntity, list, str | None]:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        history = self.history_repository.list_by_order_id(order_id)
        payment_status = self.order_repository.get_payment_status(order_id)
        return order, history, payment_status
