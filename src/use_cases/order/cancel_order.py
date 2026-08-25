from src.entities.order import OrderEntity, OrderStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.order_status_history_repository import (
    OrderStatusHistoryRepository,
)


class CancelOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        history_repository: OrderStatusHistoryRepository | None = None,
    ):
        self.order_repository = order_repository
        self.history_repository = history_repository or OrderStatusHistoryRepository(
            order_repository.db
        )

    def execute(
        self,
        order_id: int,
        changed_by_user_id: int | None = None,
    ) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        previous = order.status.value
        order.cancelar_pedido()

        try:
            self.order_repository.update_status(
                order_id, order.status.value, commit=False
            )
            self.history_repository.create(
                order_id=order_id,
                previous_status=previous,
                new_status=OrderStatus.CANCELED.value,
                changed_by_user_id=changed_by_user_id,
                note=None,
                commit=False,
            )
            self.order_repository.db.commit()
        except Exception:
            self.order_repository.db.rollback()
            raise

        updated_order = self.order_repository.get_by_id(order_id)
        if not updated_order:
            raise ValueError("Pedido não encontrado")

        return updated_order
