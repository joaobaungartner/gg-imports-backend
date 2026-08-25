from datetime import date

from src.repositories.order_repository import OrderRepository


class GetAdminOrdersSummaryUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def execute(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        return self.order_repository.admin_summary(
            date_from=date_from,
            date_to=date_to,
        )
