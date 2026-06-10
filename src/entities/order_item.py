from dataclasses import dataclass
from decimal import Decimal


@dataclass
class OrderItemEntity:
    product_id: int
    quantidade: int
    preco_unitario: Decimal
    id: int | None = None
    order_id: int | None = None

    def subtotal(self) -> Decimal:
        return self.preco_unitario * self.quantidade
