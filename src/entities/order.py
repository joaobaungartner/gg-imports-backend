from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from src.entities.order_item import OrderItemEntity


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    PREPARING = "PREPARING"
    SHIPPED = "SHIPPED"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"


VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: {OrderStatus.PAID, OrderStatus.CANCELED},
    OrderStatus.PAID: {OrderStatus.PREPARING, OrderStatus.CANCELED},
    OrderStatus.PREPARING: {
        OrderStatus.SHIPPED,
        OrderStatus.READY_FOR_PICKUP,
        OrderStatus.CANCELED,
    },
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.READY_FOR_PICKUP: {OrderStatus.DELIVERED, OrderStatus.CANCELED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELED: set(),
}

SHIPPING_METHOD_ENTREGA = "ENTREGA"
SHIPPING_METHOD_RETIRADA = "RETIRADA"


@dataclass
class OrderEntity:
    id: int | None
    client_id: int | None = None
    endereco_id: int | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    customer_cpf: str | None = None
    shipping_cep: str | None = None
    shipping_street: str | None = None
    shipping_number: str | None = None
    shipping_complement: str | None = None
    shipping_neighborhood: str | None = None
    shipping_city: str | None = None
    shipping_state: str | None = None
    shipping_method: str | None = None
    payment_method: str | None = None
    data_pedido: datetime | None = None
    updated_at: datetime | None = None
    admin_notes: str | None = None
    subtotal: Decimal = field(default_factory=lambda: Decimal("0"))
    frete: Decimal = field(default_factory=lambda: Decimal("0"))
    valor_total: Decimal = field(default_factory=lambda: Decimal("0"))
    status: OrderStatus = OrderStatus.PENDING_PAYMENT
    pagamento_id: int | None = None
    cupom_id: int | None = None
    desconto_cupom: Decimal = field(default_factory=lambda: Decimal("0"))
    ativo: bool = True
    itens: list[OrderItemEntity] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        has_legacy_refs = bool(self.client_id and self.endereco_id)
        has_checkout_data = bool(
            self.customer_name
            and self.customer_email
            and self.shipping_cep
            and self.shipping_street
            and self.shipping_number
            and self.shipping_neighborhood
            and self.shipping_city
            and self.shipping_state
        )

        if not has_legacy_refs and not has_checkout_data:
            raise ValueError("Dados do pedido incompletos")

        if self.valor_total < 0:
            raise ValueError("Valor total não pode ser negativo")

    def is_retirada(self) -> bool:
        return (self.shipping_method or "").upper() == SHIPPING_METHOD_RETIRADA

    def calcular_total(self) -> Decimal:
        subtotal = sum(
            (item.subtotal() for item in self.itens if item.ativo),
            Decimal("0"),
        )
        self.subtotal = subtotal
        total = subtotal + self.frete - self.desconto_cupom
        if total < 0:
            total = Decimal("0")
        self.valor_total = total
        return self.valor_total

    def allowed_transitions(self) -> set[OrderStatus]:
        allowed = set(VALID_TRANSITIONS.get(self.status, set()))
        if self.is_retirada():
            allowed.discard(OrderStatus.SHIPPED)
        else:
            allowed.discard(OrderStatus.READY_FOR_PICKUP)
        return allowed

    def alterar_status(
        self,
        novo_status: OrderStatus,
        *,
        force: bool = False,
    ) -> None:
        if isinstance(novo_status, str):
            novo_status = OrderStatus(novo_status)

        if novo_status == OrderStatus.SHIPPED and self.is_retirada():
            raise ValueError("Pedido de retirada não pode ser marcado como enviado")

        if novo_status == OrderStatus.READY_FOR_PICKUP and not self.is_retirada():
            raise ValueError("Pedido de entrega não pode ser marcado como pronto para retirada")

        if force:
            self.status = novo_status
            return

        allowed = self.allowed_transitions()
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
        self._validate()
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
        if OrderStatus.CANCELED in self.allowed_transitions():
            self.alterar_status(OrderStatus.CANCELED)
        else:
            self.status = OrderStatus.CANCELED

    def confirmar_pedido(self) -> None:
        if len(self.itens) < 1:
            raise ValueError("Pedido sem itens")
        self.validar_pedido()
        self.alterar_status(OrderStatus.PAID)

    def marcar_como_pago(self) -> None:
        self.alterar_status(OrderStatus.PAID)

    def marcar_como_enviado(self) -> None:
        self.alterar_status(OrderStatus.SHIPPED)

    def marcar_como_entregue(self) -> None:
        self.alterar_status(OrderStatus.DELIVERED)
