from src.entities.payment import PaymentEntity, PaymentStatus
from src.repositories.payment_repository import PaymentRepository


class UpdatePaymentStatusUseCase:
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(self, payment_id: int, novo_status: str) -> PaymentEntity:
        payment = self.payment_repository.get_by_id(payment_id)
        if not payment:
            raise ValueError("Pagamento não encontrado")

        try:
            status = PaymentStatus(novo_status)
        except ValueError as exc:
            raise ValueError("Status de pagamento inválido") from exc

        payment.alterar_status(status)

        updated_payment = self.payment_repository.update_status(
            payment_id, payment.status.value
        )
        if not updated_payment:
            raise ValueError("Pagamento não encontrado")

        return updated_payment
