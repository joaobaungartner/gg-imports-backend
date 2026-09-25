from datetime import datetime
from src.entities.order import OrderStatus

from src.repositories.order_repository import OrderRepository
from src.repositories.order_status_history_repository import OrderStatusHistoryRepository
from src.repositories.product_repository import ProductRepository
from src.use_cases.order.cancel_order import CancelOrderUseCase


class ExpireStockReservationsUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        history_repository: OrderStatusHistoryRepository,
    ):
        self.order_repository = order_repository
        self.product_repository = product_repository
        self.history_repository = history_repository

    def execute(self, now: datetime | None = None) -> list[int]:
        now = now or datetime.utcnow()
        expired_ids = self.order_repository.list_expired_reservations(now)
        cancel = CancelOrderUseCase(
            self.order_repository,
            self.history_repository,
            self.product_repository,
        )
        canceled_ids = []
        for order_id in expired_ids:
            if cancel.execute(order_id, expired_before=now).status == OrderStatus.CANCELED:
                canceled_ids.append(order_id)
        return canceled_ids
