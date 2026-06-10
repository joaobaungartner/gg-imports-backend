from decimal import Decimal

from src.entities.order import OrderStatus
from src.entities.order_item import OrderItemEntity
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_repository import OrderRepository
from src.use_cases.order.calculate_order_total import CalculateOrderTotalUseCase


class CreateOrderItemUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        order_item_repository: OrderItemRepository,
    ):
        self.order_repository = order_repository
        self.order_item_repository = order_item_repository
        # TODO: injetar ProductRepository quando disponível
        # TODO: converter itens do Carrinho no checkout

    def _resolve_item_price(self, product_id: int) -> Decimal:
        # TODO: ProductRepository - validar produto ativo e obter preço atual
        return Decimal("0")

    def execute(
        self,
        order_id: int,
        product_id: int,
        quantidade: int,
    ) -> OrderItemEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        if order.status != OrderStatus.PENDING:
            raise ValueError("Pedido não permite alteração de itens")

        if quantidade <= 0:
            raise ValueError("Quantidade inválida")

        # TODO: ProductRepository - validar se produto existe
        # TODO: ProductRepository - validar se produto está ativo
        # TODO: ProductRepository - validar estoque suficiente

        preco_unitario = self._resolve_item_price(product_id)

        item = OrderItemEntity(
            id=None,
            order_id=order_id,
            product_id=product_id,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
        )

        created_item = self.order_item_repository.create(item)

        CalculateOrderTotalUseCase(self.order_repository).execute(order_id)

        return created_item
