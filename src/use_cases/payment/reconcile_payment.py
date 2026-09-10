from datetime import datetime
from decimal import Decimal

from src.entities.payment import PaymentStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.payment_repository import PaymentRepository
from src.use_cases.payment.confirm_payment import ConfirmPaymentUseCase


STATUS_MAP = {
    "pending": PaymentStatus.PENDING,
    "in_process": PaymentStatus.PROCESSING,
    "authorized": PaymentStatus.PROCESSING,
    "approved": PaymentStatus.PAID,
    "rejected": PaymentStatus.FAILED,
    "cancelled": PaymentStatus.CANCELED,
    "refunded": PaymentStatus.REFUNDED,
    "charged_back": PaymentStatus.REFUNDED,
}


class ReconcilePaymentUseCase:
    def __init__(self, payments: PaymentRepository, orders: OrderRepository):
        self.payments = payments
        self.orders = orders

    def execute(self, gateway_data: dict):
        gateway_id = str(gateway_data.get("id") or "")
        metadata = gateway_data.get("metadata") or {}
        local_id = metadata.get("payment_id")
        payment = self.payments.get_by_id(int(local_id)) if local_id else None
        if not payment:
            payment = self.payments.get_by_transaction_code(gateway_id)
        if not payment:
            raise ValueError("Pagamento local não encontrado")

        external_reference = str(gateway_data.get("external_reference") or "")
        if external_reference != str(payment.order_id):
            raise ValueError("Referência do pagamento não confere")
        gateway_amount = Decimal(str(gateway_data.get("transaction_amount") or 0))
        if gateway_amount != payment.valor:
            raise ValueError("Valor recebido do gateway não confere")

        gateway_status = str(gateway_data.get("status") or "")
        local_status = STATUS_MAP.get(gateway_status)
        if not local_status:
            raise ValueError("Status desconhecido do Mercado Pago")

        common = {
            "codigo_transacao": gateway_id,
            "gateway": "MERCADO_PAGO",
            "gateway_status": gateway_status,
            "status_detail": gateway_data.get("status_detail"),
            "payment_method_id": gateway_data.get("payment_method_id"),
            "installments": gateway_data.get("installments"),
            "last_reconciled_at": datetime.utcnow(),
        }
        if local_status == PaymentStatus.PAID:
            self.payments.update(payment.id, common)
            return ConfirmPaymentUseCase(self.payments, self.orders).execute(payment.id, gateway_id)

        if payment.status in (PaymentStatus.PAID, PaymentStatus.REFUNDED):
            if local_status != PaymentStatus.REFUNDED:
                return self.payments.get_by_id(payment.id)
        common["status"] = local_status.value
        if local_status == PaymentStatus.REFUNDED:
            common["refunded_amount"] = payment.valor
        updated = self.payments.update(payment.id, common)
        if local_status in (PaymentStatus.CANCELED, PaymentStatus.REFUNDED):
            from src.entities.order import OrderStatus
            from src.use_cases.order.cancel_order import CancelOrderUseCase

            order = self.orders.get_by_id(payment.order_id)
            if order and order.status in (
                OrderStatus.PENDING_PAYMENT,
                OrderStatus.PAID,
                OrderStatus.PREPARING,
                OrderStatus.READY_FOR_PICKUP,
            ):
                CancelOrderUseCase(self.orders).execute(payment.order_id)
        return updated
