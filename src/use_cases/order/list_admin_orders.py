from datetime import date

from src.repositories.order_repository import OrderRepository


class ListAdminOrdersUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def execute(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        shipping_method: str | None = None,
        payment_status: str | None = None,
        payment_method: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        sort: str = "desc",
    ) -> dict:
        return self.order_repository.list_admin_paginated(
            page=page,
            page_size=page_size,
            status=status,
            shipping_method=shipping_method,
            payment_status=payment_status,
            payment_method=payment_method,
            date_from=date_from,
            date_to=date_to,
            search=search,
            sort=sort if sort in ("asc", "desc") else "desc",
        )
