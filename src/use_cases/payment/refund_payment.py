import uuid

from src.config.config import get_settings
from src.entities.payment import PaymentEntity, PaymentStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.payment_repository import PaymentRepository
from src.services.mercado_pago import MercadoPagoGateway
from src.use_cases.payment.reconcile_payment import ReconcilePaymentUseCase


class RefundPaymentUseCase:
    def __init__(self, payment_repository: PaymentRepository, order_repository: OrderRepository, gateway: MercadoPagoGateway | None = None):
        self.payment_repository = payment_repository
        self.order_repository = order_repository
        settings = get_settings()
        if gateway is None:
            if not settings.MERCADO_PAGO_ACCESS_TOKEN:
                raise ValueError("Mercado Pago não configurado")
            gateway = MercadoPagoGateway(settings.MERCADO_PAGO_ACCESS_TOKEN, settings.MERCADO_PAGO_API_BASE_URL)
        self.gateway = gateway

    def execute(self, payment_id: int) -> PaymentEntity:
        payment = self.payment_repository.get_by_id(payment_id)
        if not payment:
            raise ValueError("Pagamento não encontrado")
        if payment.status == PaymentStatus.REFUNDED:
            return payment
        if payment.status != PaymentStatus.PAID or not payment.codigo_transacao:
            raise ValueError("Pagamento não pode ser estornado")
        # Stable across retries, timeouts and concurrent webhook deliveries.
        key = str(uuid.uuid5(uuid.NAMESPACE_URL, f"gg-imports:refund:{payment.id}:{payment.codigo_transacao}"))
        self.gateway.refund(payment.codigo_transacao, key)
        gateway_data = self.gateway.get_payment(payment.codigo_transacao)
        if gateway_data.get("status") != "refunded":
            raise RuntimeError("Estorno ainda não confirmado pelo Mercado Pago")
        return ReconcilePaymentUseCase(self.payment_repository, self.order_repository, self.gateway).execute(gateway_data)
