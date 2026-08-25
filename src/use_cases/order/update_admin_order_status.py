from src.entities.order import OrderEntity, OrderStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.order_status_history_repository import (
    OrderStatusHistoryRepository,
)
from src.repositories.product_repository import ProductRepository
from src.use_cases.order.cancel_order import CancelOrderUseCase


class UpdateAdminOrderStatusUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        history_repository: OrderStatusHistoryRepository,
        product_repository: ProductRepository | None = None,
    ):
        self.order_repository = order_repository
        self.history_repository = history_repository
        self.product_repository = product_repository or ProductRepository(
            order_repository.db
        )

    def execute(
        self,
        order_id: int,
        novo_status: str,
        admin_user_id: int,
        note: str | None = None,
        force: bool = False,
    ) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        try:
            status = OrderStatus(novo_status)
        except ValueError as exc:
            raise ValueError("Status de pedido inválido") from exc

        if status == order.status:
            raise ValueError("O pedido já está neste status")

        if status == OrderStatus.CANCELED:
            return CancelOrderUseCase(
                self.order_repository,
                self.history_repository,
                self.product_repository,
            ).execute(order_id, changed_by_user_id=admin_user_id)

        if order.status == OrderStatus.CANCELED:
            raise ValueError("Pedido cancelado não pode ser reativado")

        needs_force = order.status in (OrderStatus.DELIVERED, OrderStatus.CANCELED)
        if needs_force and not force:
            raise ValueError(
                "Confirmação explícita necessária para alterar pedido "
                "entregue ou cancelado"
            )

        previous = order.status.value
        order.alterar_status(status, force=force or needs_force)

        try:
            self.order_repository.update_status(
                order_id, order.status.value, commit=False
            )
            self.history_repository.create(
                order_id=order_id,
                previous_status=previous,
                new_status=order.status.value,
                changed_by_user_id=admin_user_id,
                note=note,
                commit=False,
            )
            self.order_repository.db.commit()
        except Exception:
            self.order_repository.db.rollback()
            raise

        updated = self.order_repository.get_by_id(order_id)
        if not updated:
            raise ValueError("Pedido não encontrado")
        return updated
