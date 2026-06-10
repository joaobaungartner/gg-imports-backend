from src.entities.order import OrderStatus
from src.entities.payment import PaymentEntity
from src.repositories.order_repository import OrderRepository
from src.repositories.payment_repository import PaymentRepository


class ConfirmPaymentUseCase:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        order_repository: OrderRepository,
    ):
        self.payment_repository = payment_repository
        self.order_repository = order_repository

    def execute(self, payment_id: int, codigo_transacao: str) -> PaymentEntity:
        payment = self.payment_repository.get_by_id(payment_id)
        if not payment:
            raise ValueError("Pagamento não encontrado")

        payment.confirmar_pagamento(codigo_transacao)

        updated_payment = self.payment_repository.update(
            payment_id,
            {
                "status": payment.status.value,
                "codigo_transacao": payment.codigo_transacao,
                "data_pagamento": payment.data_pagamento,
            },
        )
        if not updated_payment:
            raise ValueError("Pagamento não encontrado")

        order = self.order_repository.get_by_id(payment.order_id)
        if order and order.status == OrderStatus.CONFIRMED:
            order.marcar_como_pago()
            self.order_repository.update_status(
                payment.order_id, order.status.value
            )

        return updated_payment
