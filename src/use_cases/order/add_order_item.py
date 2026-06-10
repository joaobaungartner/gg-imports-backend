from decimal import Decimal

from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.repositories.order_repository import OrderRepository


class AddOrderItemUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
        # TODO: injetar ProductRepository quando disponível

    def _resolve_item_price(self, product_id: int) -> Decimal:
        # TODO: integrar ProductRepository para validar produto e obter preço
        return Decimal("0")

    def execute(
        self,
        order_id: int,
        product_id: int,
        quantidade: int,
    ) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        if order.status not in (OrderStatus.PENDING,):
            raise ValueError("Pedido não pode ser alterado")

        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")

        # TODO: ProductRepository - validar produto ativo e estoque
        preco_unitario = self._resolve_item_price(product_id)

        item = OrderItemEntity(
            product_id=product_id,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
        )
        order.adicionar_item(item)

        self.order_repository.add_item(order_id, item)

        updated_order = self.order_repository.update(
            order_id, {"valor_total": order.valor_total}
        )
        if not updated_order:
            raise ValueError("Pedido não encontrado")

        return updated_order
