from datetime import datetime

from src.entities.order import OrderStatus
from src.entities.payment import PaymentEntity, PaymentStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.payment_repository import PaymentRepository
from src.repositories.order_status_history_repository import OrderStatusHistoryRepository
from src.repositories.notification_repository import NotificationRepository
from src.services.notification_service import NotificationService
from src.services.mercado_pago import MercadoPagoGateway
from src.use_cases.order.cancel_order import CancelOrderUseCase


LATE_REFUND_PENDING = "late_payment_refund_pending"


class LatePaymentRefundPending(RuntimeError):
    """The approval was persisted; a retry must finish the refund."""


class ConfirmPaymentUseCase:
    def __init__(self, payment_repository: PaymentRepository,
                 order_repository: OrderRepository, gateway: MercadoPagoGateway | None = None):
        self.payment_repository = payment_repository
        self.order_repository = order_repository
        self.gateway = gateway

    def execute(self, payment_id: int, codigo_transacao: str, *,
                gateway_fields: dict | None = None) -> PaymentEntity:
        db = self.order_repository.db
        try:
            payment = self.payment_repository.get_by_id(payment_id)
            if not payment:
                raise ValueError("Pagamento não encontrado")
            # Lock the order before the payment, just as reservation cancellation does.
            order = self.order_repository.get_by_id_for_update(payment.order_id)
            payment = self.payment_repository.get_by_id_for_update(payment_id)
            if not order:
                raise ValueError("Pedido não encontrado")
            if payment.codigo_transacao and payment.codigo_transacao != codigo_transacao:
                raise ValueError("Pagamento já associado a outra transação")
            if payment.status == PaymentStatus.REFUNDED:
                db.commit()
                return payment

            now = datetime.utcnow()
            expired = (order.status == OrderStatus.PENDING_PAYMENT
                       and order.reserva_expira_em is not None
                       and order.reserva_expira_em <= now)
            if expired:
                order = CancelOrderUseCase(self.order_repository).execute(order.id, commit=False)
            late = order.status == OrderStatus.CANCELED
            was_refund_pending = payment.status_detail == LATE_REFUND_PENDING
            if late:
                # Gateway approval is authoritative even after local cancellation.
                payment.status = PaymentStatus.PAID
                payment.codigo_transacao = codigo_transacao
                payment.data_pagamento = payment.data_pagamento or now
            else:
                payment.confirmar_pagamento(codigo_transacao)

            fields = dict(gateway_fields or {})
            fields.update(status=payment.status.value, codigo_transacao=codigo_transacao,
                          data_pagamento=payment.data_pagamento)
            if late:
                fields["status_detail"] = LATE_REFUND_PENDING
            updated = self.payment_repository.update(payment_id, fields, commit=False)
            notifications = NotificationService(NotificationRepository(db))
            if late and not was_refund_pending and order.customer_email:
                notifications.email(
                    "LATE_PAYMENT_REFUND_PENDING", order.customer_email,
                    f"Estorno em processamento — pedido #{order.id}",
                    "O pagamento foi aprovado após o cancelamento ou vencimento da reserva. "
                    "O pedido permanece cancelado e o estorno está em processamento.", commit=False)
            elif not late and order.status == OrderStatus.PENDING_PAYMENT:
                self.order_repository.update_status(order.id, OrderStatus.PAID.value, commit=False)
                OrderStatusHistoryRepository(db).create(
                    order_id=order.id, previous_status=order.status.value,
                    new_status=OrderStatus.PAID.value, commit=False)
                if order.customer_email:
                    notifications.email(
                        "PAYMENT_APPROVED", order.customer_email,
                        f"Pagamento aprovado — pedido #{order.id}",
                        "Seu pagamento foi aprovado e o pedido seguirá para preparação.", commit=False)
            # Payment, order, stock and notification commit together before external I/O.
            db.commit()
        except Exception:
            db.rollback()
            raise

        if late:
            from src.use_cases.payment.refund_payment import RefundPaymentUseCase
            try:
                return RefundPaymentUseCase(
                    self.payment_repository, self.order_repository, self.gateway).execute(payment_id)
            except (ValueError, RuntimeError) as exc:
                raise LatePaymentRefundPending(
                    "Pagamento tardio registrado; estorno pendente. Reprocesse a conciliação."
                ) from exc
        return updated
