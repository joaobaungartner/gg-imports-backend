import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, Enum):
    PIX = "PIX"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    BOLETO = "BOLETO"


VALID_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.PENDING: {
        PaymentStatus.PROCESSING,
        PaymentStatus.PAID,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELED,
    },
    PaymentStatus.PROCESSING: {
        PaymentStatus.PAID,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELED,
    },
    PaymentStatus.PAID: {PaymentStatus.REFUNDED},
    PaymentStatus.FAILED: set(),
    PaymentStatus.CANCELED: set(),
    PaymentStatus.REFUNDED: set(),
}


@dataclass
class PaymentEntity:
    id: int | None
    order_id: int
    metodo: PaymentMethod | str
    valor: Decimal
    status: PaymentStatus = PaymentStatus.PENDING
    codigo_transacao: str | None = None
    data_pagamento: datetime | None = None
    ativo: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.metodo, str):
            self.metodo = PaymentMethod(self.metodo)
        if isinstance(self.valor, (int, float)):
            self.valor = Decimal(str(self.valor))
        self.validar_pagamento()

    def validar_pagamento(self) -> None:
        if not self.order_id:
            raise ValueError("Pedido não encontrado")
        if self.valor <= 0:
            raise ValueError("Valor do pagamento inválido")
        if not self.metodo:
            raise ValueError("Método de pagamento inválido")

    def alterar_status(self, novo_status: PaymentStatus) -> None:
        if isinstance(novo_status, str):
            novo_status = PaymentStatus(novo_status)

        allowed = VALID_TRANSITIONS.get(self.status, set())
        if novo_status not in allowed:
            raise ValueError("Transição de status inválida")

        self.status = novo_status

    def gerar_codigo_transacao(self) -> str:
        return f"GG-{uuid.uuid4().hex[:12].upper()}"

    def processar_pagamento(self) -> None:
        if self.status != PaymentStatus.PENDING:
            raise ValueError("Pagamento não pode ser processado")
        self.alterar_status(PaymentStatus.PROCESSING)

    def confirmar_pagamento(self, codigo_transacao: str) -> None:
        if self.status == PaymentStatus.PAID:
            raise ValueError("Pagamento já confirmado")
        if not codigo_transacao:
            raise ValueError("Código de transação é obrigatório")

        if self.status == PaymentStatus.PENDING:
            self.alterar_status(PaymentStatus.PROCESSING)

        self.codigo_transacao = codigo_transacao
        self.data_pagamento = datetime.utcnow()
        self.alterar_status(PaymentStatus.PAID)

    def cancelar_pagamento(self) -> None:
        if self.status not in (PaymentStatus.PENDING, PaymentStatus.PROCESSING):
            raise ValueError("Pagamento não pode ser cancelado")
        self.alterar_status(PaymentStatus.CANCELED)

    def estornar_pagamento(self) -> None:
        if self.status != PaymentStatus.PAID:
            raise ValueError("Pagamento não pode ser estornado")
        self.alterar_status(PaymentStatus.REFUNDED)

    def esta_pago(self) -> bool:
        return self.status == PaymentStatus.PAID

    def esta_pendente(self) -> bool:
        return self.status == PaymentStatus.PENDING

    def esta_cancelado(self) -> bool:
        return self.status == PaymentStatus.CANCELED

    def esta_recusado(self) -> bool:
        return self.status == PaymentStatus.FAILED
