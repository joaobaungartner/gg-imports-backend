from src.entities.payment import PaymentEntity
from src.repositories.payment_repository import PaymentRepository


class CancelPaymentUseCase:
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    def execute(self, payment_id: int) -> PaymentEntity:
        payment = self.payment_repository.get_by_id(payment_id)
        if not payment:
            raise ValueError("Pagamento não encontrado")

        payment.cancelar_pagamento()

        updated_payment = self.payment_repository.update_status(
            payment_id, payment.status.value
        )
        if not updated_payment:
            raise ValueError("Pagamento não encontrado")

        # TODO: cancelar pedido associado, se essa for a regra do projeto
        # Exemplo futuro:
        # self.order_repository.cancel(order_id)

        return updated_payment
