from src.entities.payment import PaymentEntity
from src.repositories.payment_repository import PaymentRepository


class ProcessPaymentUseCase:
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    def execute(self, payment_id: int) -> PaymentEntity:
        payment = self.payment_repository.get_by_id(payment_id)
        if not payment:
            raise ValueError("Pagamento não encontrado")

        payment.processar_pagamento()

        # TODO: integrar com gateway de pagamento
        # Exemplos futuros: Mercado Pago, Stripe, Pagar.me, PagSeguro
        # O gateway deve retornar token/identificador seguro, nunca dados de cartão.
        # Exemplo futuro:
        # gateway_response = self.payment_gateway.process(payment)
        # payment.codigo_transacao = gateway_response.transaction_id

        updated_payment = self.payment_repository.update_status(
            payment_id, payment.status.value
        )
        if not updated_payment:
            raise ValueError("Pagamento não encontrado")

        return updated_payment
