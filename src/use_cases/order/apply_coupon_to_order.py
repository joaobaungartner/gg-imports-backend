from decimal import Decimal

from src.entities.order import OrderEntity, OrderStatus
from src.repositories.coupon_repository import CouponRepository
from src.repositories.order_repository import OrderRepository


class ApplyCouponToOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        coupon_repository: CouponRepository,
    ):
        self.order_repository = order_repository
        self.coupon_repository = coupon_repository

    def execute(self, order_id: int, cupom_id: int) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise ValueError("Pedido não pode ser alterado")

        coupon = self.coupon_repository.get_by_id(cupom_id)
        if not coupon:
            raise ValueError("Cupom não encontrado")

        subtotal = sum(
            (item.subtotal() for item in order.itens), Decimal("0")
        )
        desconto_aplicado, _ = coupon.calcular_desconto(subtotal)
        order.aplicar_cupom(cupom_id, desconto_aplicado)

        updated_order = self.order_repository.update(
            order_id,
            {
                "cupom_id": order.cupom_id,
                "desconto_cupom": order.desconto_cupom,
                "valor_total": order.valor_total,
            },
        )
        if not updated_order:
            raise ValueError("Pedido não encontrado")

        return updated_order
