from src.entities.payment import PaymentEntity
from src.repositories.payment_repository import PaymentRepository


class RefundPaymentUseCase:
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    def execute(self, payment_id: int) -> PaymentEntity:
        payment = self.payment_repository.get_by_id(payment_id)
        if not payment:
            raise ValueError("Pagamento não encontrado")

        payment.estornar_pagamento()

        updated_payment = self.payment_repository.update_status(
            payment_id, payment.status.value
        )
        if not updated_payment:
            raise ValueError("Pagamento não encontrado")

        # TODO: integrar com gateway de pagamento para estorno
        # Exemplos futuros: Mercado Pago, Stripe, Pagar.me, PagSeguro

        # TODO: atualizar status do pedido associado, se essa for a regra do projeto

        return updated_payment
