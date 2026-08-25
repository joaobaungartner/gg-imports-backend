from src.repositories.order_status_history_repository import (
    OrderStatusHistoryRepository,
)


class GetOrderStatusHistoryUseCase:
    def __init__(self, history_repository: OrderStatusHistoryRepository):
        self.history_repository = history_repository

    def execute(self, order_id: int):
        return self.history_repository.list_by_order_id(order_id)
