from src.entities.order import OrderEntity, OrderStatus
from src.repositories.client_repository import ClientRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.order_status_history_repository import (
    OrderStatusHistoryRepository,
)
from src.use_cases.address.validate_address_for_order import (
    ValidateAddressForOrderUseCase,
)


class ConfirmOrderUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        order_repository: OrderRepository,
        validate_address_use_case: ValidateAddressForOrderUseCase,
    ):
        self.client_repository = client_repository
        self.order_repository = order_repository
        self.validate_address_use_case = validate_address_use_case
        # TODO: injetar ProductRepository quando disponível

    def execute(self, order_id: int) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        client = self.client_repository.get_by_id(order.client_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        if not client.ativo:
            raise ValueError("Cliente inativo")

        self.validate_address_use_case.execute(order.endereco_id, order.client_id)

        # TODO: integrar ProductRepository para validar estoque dos itens
        # Exemplo futuro:
        # for item in order.itens:
        #     product = self.product_repository.get_by_id(item.product_id)
        #     if not product or product.estoque < item.quantidade:
        #         raise ValueError("Estoque insuficiente")

        order.confirmar_pedido()

        previous = OrderStatus.PENDING_PAYMENT.value
        history_repo = OrderStatusHistoryRepository(self.order_repository.db)
        try:
            self.order_repository.update_status(
                order_id, order.status.value, commit=False
            )
            history_repo.create(
                order_id=order_id,
                previous_status=previous,
                new_status=order.status.value,
                changed_by_user_id=None,
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
