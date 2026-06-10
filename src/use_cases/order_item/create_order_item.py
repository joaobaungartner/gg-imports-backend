from decimal import Decimal

from src.entities.order import OrderStatus
from src.entities.order_item import OrderItemEntity
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.use_cases.order.calculate_order_total import CalculateOrderTotalUseCase
from src.use_cases.product.check_product_availability import (
    CheckProductAvailabilityUseCase,
)


class CreateOrderItemUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        order_item_repository: OrderItemRepository,
        product_repository: ProductRepository,
    ):
        self.order_repository = order_repository
        self.order_item_repository = order_item_repository
        self.product_repository = product_repository
        self._check_availability = CheckProductAvailabilityUseCase(
            product_repository
        )
        # TODO: converter itens do Carrinho no checkout

    def _resolve_item_price(
        self, product_id: int, quantidade: int
    ) -> Decimal:
        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")
        if not product.ativo:
            raise ValueError("Produto inativo")

        availability = self._check_availability.execute(product_id, quantidade)
        if not availability.disponivel:
            raise ValueError("Estoque insuficiente")

        return product.preco

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

        preco_unitario = self._resolve_item_price(product_id, quantidade)

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
