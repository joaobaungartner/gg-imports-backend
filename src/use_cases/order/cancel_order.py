from src.entities.order import OrderEntity, OrderStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.order_status_history_repository import (
    OrderStatusHistoryRepository,
)


class CancelOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        history_repository: OrderStatusHistoryRepository | None = None,
        product_repository: ProductRepository | None = None,
    ):
        self.order_repository = order_repository
        self.history_repository = history_repository or OrderStatusHistoryRepository(
            order_repository.db
        )
        self.product_repository = product_repository or ProductRepository(
            order_repository.db
        )

    def execute(
        self,
        order_id: int,
        changed_by_user_id: int | None = None,
    ) -> OrderEntity:
        order = self.order_repository.get_by_id_for_update(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        if order.status == OrderStatus.CANCELED:
            return order

        previous = order.status.value
        order.cancelar_pedido()

        try:
            if order.estoque_reservado:
                for item in order.itens:
                    if item.ativo:
                        self.product_repository.release_stock(
                            item.product_id, item.quantidade
                        )
                self.order_repository.release_reservation(order_id)
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
