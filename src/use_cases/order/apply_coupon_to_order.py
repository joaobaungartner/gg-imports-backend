from decimal import Decimal

from src.entities.order import OrderEntity, OrderStatus
from src.repositories.order_repository import OrderRepository


class ApplyCouponToOrderUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
        # TODO: injetar CouponRepository quando disponível

    def _resolve_coupon_discount(self, cupom_id: int) -> Decimal:
        # TODO: integrar CouponRepository para validar cupom ativo e validade
        # Exemplo futuro:
        # coupon = self.coupon_repository.get_by_id(cupom_id)
        # if not coupon or not coupon.ativo:
        #     raise ValueError("Cupom inválido")
        # return coupon.desconto
        return Decimal("0")

    def execute(self, order_id: int, cupom_id: int) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise ValueError("Pedido não pode ser alterado")

        desconto = self._resolve_coupon_discount(cupom_id)
        order.aplicar_cupom(cupom_id, desconto)

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
