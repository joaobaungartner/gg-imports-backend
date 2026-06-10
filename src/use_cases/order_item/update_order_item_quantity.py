from src.entities.order import OrderStatus
from src.entities.order_item import OrderItemEntity
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_repository import OrderRepository
from src.use_cases.order.calculate_order_total import CalculateOrderTotalUseCase


class UpdateOrderItemQuantityUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        order_item_repository: OrderItemRepository,
    ):
        self.order_repository = order_repository
        self.order_item_repository = order_item_repository
        # TODO: injetar ProductRepository para validar estoque

    def execute(self, order_item_id: int, quantidade: int) -> OrderItemEntity:
        item = self.order_item_repository.get_by_id(order_item_id)
        if not item:
            raise ValueError("Item do pedido não encontrado")

        if not item.ativo:
            raise ValueError("Item do pedido não encontrado")

        order = self.order_repository.get_by_id(item.order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        if order.status != OrderStatus.PENDING:
            raise ValueError("Pedido não permite alteração de itens")

        if quantidade <= 0:
            raise ValueError("Quantidade inválida")

        # TODO: ProductRepository - validar estoque suficiente

        item.atualizar_quantidade(quantidade)

        updated_item = self.order_item_repository.update_quantity(
            order_item_id, quantidade
        )
        if not updated_item:
            raise ValueError("Item do pedido não encontrado")

        CalculateOrderTotalUseCase(self.order_repository).execute(item.order_id)

        return updated_item
