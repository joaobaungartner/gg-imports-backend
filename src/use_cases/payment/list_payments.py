from src.entities.payment import PaymentEntity
from src.repositories.payment_repository import PaymentRepository


class ListPaymentsUseCase:
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(
        self,
        status: str | None = None,
        metodo: str | None = None,
    ) -> list[PaymentEntity]:
        if status:
            payments = self.payment_repository.list_by_status(status)
        else:
            payments = self.payment_repository.list_all()

        if metodo:
            return [
                payment
                for payment in payments
                if (
                    payment.metodo.value
                    if hasattr(payment.metodo, "value")
                    else payment.metodo
                )
                == metodo
            ]

        return payments
