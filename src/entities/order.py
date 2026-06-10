from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from src.entities.order_item import OrderItemEntity


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"


VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELED},
    OrderStatus.CONFIRMED: {OrderStatus.PAID, OrderStatus.CANCELED},
    OrderStatus.PAID: {OrderStatus.PROCESSING},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELED: set(),
}


@dataclass
class OrderEntity:
    id: int | None
    client_id: int
    endereco_id: int
    data_pedido: datetime | None = None
    valor_total: Decimal = field(default_factory=lambda: Decimal("0"))
    status: OrderStatus = OrderStatus.PENDING
    pagamento_id: int | None = None
    cupom_id: int | None = None
    desconto_cupom: Decimal = field(default_factory=lambda: Decimal("0"))
    ativo: bool = True
    itens: list[OrderItemEntity] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.client_id:
            raise ValueError("Cliente não encontrado")
        if not self.endereco_id:
            raise ValueError("Endereço não encontrado")
        if self.valor_total < 0:
            raise ValueError("Valor total não pode ser negativo")

    def calcular_total(self) -> Decimal:
        subtotal = sum(
            (item.subtotal() for item in self.itens if item.ativo),
            Decimal("0"),
        )
        total = subtotal - self.desconto_cupom
        if total < 0:
            total = Decimal("0")
        self.valor_total = total
        return self.valor_total

    def alterar_status(self, novo_status: OrderStatus) -> None:
        if isinstance(novo_status, str):
            novo_status = OrderStatus(novo_status)

        allowed = VALID_TRANSITIONS.get(self.status, set())
        if novo_status not in allowed:
            raise ValueError("Transição de status inválida")

        self.status = novo_status

    def adicionar_item(self, item: OrderItemEntity) -> None:
        if item.quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        if item.product_id <= 0:
            raise ValueError("Produto inválido")
        self.itens.append(item)
        self.calcular_total()

    def remover_item(self, item_id: int) -> None:
        itens_filtrados = [item for item in self.itens if item.id != item_id]
        if len(itens_filtrados) == len(self.itens):
            raise ValueError("Item não encontrado")
        self.itens = itens_filtrados
        self.calcular_total()

    def aplicar_cupom(self, cupom_id: int, desconto: Decimal) -> None:
        if desconto < 0:
            raise ValueError("Cupom inválido")
        self.cupom_id = cupom_id
        self.desconto_cupom = desconto
        self.calcular_total()

    def validar_pedido(self) -> None:
        if not self.client_id:
            raise ValueError("Cliente não encontrado")
        if not self.endereco_id:
            raise ValueError("Endereço não encontrado")
        if self.valor_total < 0:
            raise ValueError("Valor total não pode ser negativo")

    def can_cancel(self) -> bool:
        return self.status not in (
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELED,
        )

    def cancelar_pedido(self) -> None:
        if not self.can_cancel():
            raise ValueError("Pedido não pode ser cancelado")
        if self.status in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            self.alterar_status(OrderStatus.CANCELED)
        else:
            self.status = OrderStatus.CANCELED

    def confirmar_pedido(self) -> None:
        if len(self.itens) < 1:
            raise ValueError("Pedido sem itens")
        self.validar_pedido()
        self.alterar_status(OrderStatus.CONFIRMED)

    def marcar_como_pago(self) -> None:
        self.alterar_status(OrderStatus.PAID)

    def marcar_como_enviado(self) -> None:
        self.alterar_status(OrderStatus.SHIPPED)

    def marcar_como_entregue(self) -> None:
        self.alterar_status(OrderStatus.DELIVERED)
