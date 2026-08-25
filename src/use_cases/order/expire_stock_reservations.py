from datetime import datetime

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
        expired_ids = self.order_repository.list_expired_reservations(
            now or datetime.utcnow()
        )
        cancel = CancelOrderUseCase(
            self.order_repository,
            self.history_repository,
            self.product_repository,
        )
        for order_id in expired_ids:
            cancel.execute(order_id)
        return expired_ids
