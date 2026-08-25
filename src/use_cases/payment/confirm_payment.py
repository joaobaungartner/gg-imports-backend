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
        if order and order.status == OrderStatus.PENDING_PAYMENT:
            previous = order.status.value
            order.marcar_como_pago()
            from src.repositories.order_status_history_repository import (
                OrderStatusHistoryRepository,
            )

            history_repo = OrderStatusHistoryRepository(self.order_repository.db)
            try:
                self.order_repository.update_status(
                    payment.order_id, order.status.value, commit=False
                )
                history_repo.create(
                    order_id=payment.order_id,
                    previous_status=previous,
                    new_status=order.status.value,
                    changed_by_user_id=None,
                    note=None,
                    commit=False,
                )
                self.order_repository.db.commit()
            except Exception:
                self.order_repository.db.rollback()
                raise

        return updated_payment
