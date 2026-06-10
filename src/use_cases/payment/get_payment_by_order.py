from src.entities.payment import PaymentEntity
from src.repositories.payment_repository import PaymentRepository


class GetPaymentByOrderUseCase:
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    def execute(self, order_id: int) -> PaymentEntity:
        payment = self.payment_repository.get_by_order_id(order_id)
        if not payment:
            raise ValueError("Pagamento não encontrado")
        return payment
