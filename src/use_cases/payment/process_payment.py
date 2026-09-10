import uuid
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from src.config.config import get_settings
from src.entities.payment import PaymentEntity, PaymentMethod, PaymentStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.payment_repository import PaymentRepository
from src.services.mercado_pago import MercadoPagoGateway
from src.use_cases.payment.reconcile_payment import ReconcilePaymentUseCase


class ProcessPaymentUseCase:
    def __init__(self, payment_repository: PaymentRepository, order_repository: OrderRepository, gateway: MercadoPagoGateway | None = None):
        self.payment_repository = payment_repository
        self.order_repository = order_repository
        settings = get_settings()
        if gateway is None:
            if not settings.MERCADO_PAGO_ACCESS_TOKEN:
                raise ValueError("Mercado Pago não configurado")
            gateway = MercadoPagoGateway(settings.MERCADO_PAGO_ACCESS_TOKEN, settings.MERCADO_PAGO_API_BASE_URL)
        self.gateway = gateway
        self.settings = settings

    def execute(self, payment_id: int, card_data: dict[str, Any] | None = None) -> PaymentEntity:
        payment = self.payment_repository.get_by_id_for_update(payment_id)
        if not payment:
            raise ValueError("Pagamento não encontrado")
        if payment.status == PaymentStatus.PAID:
            return payment
        if payment.codigo_transacao and payment.status in (PaymentStatus.PENDING, PaymentStatus.PROCESSING):
            return ReconcilePaymentUseCase(self.payment_repository, self.order_repository).execute(
                self.gateway.get_payment(payment.codigo_transacao)
            )

        order = self.order_repository.get_by_id(payment.order_id)
        if not order or not order.ativo or order.status.value != "PENDING_PAYMENT":
            raise ValueError("Pedido não está disponível para pagamento")

        idempotency_key = (
            str(uuid.uuid4())
            if payment.status == PaymentStatus.FAILED
            else payment.idempotency_key or str(uuid.uuid4())
        )
        payload: dict[str, Any] = {
            "transaction_amount": float(payment.valor),
            "description": f"Pedido #{order.id} - GG Imports",
            "external_reference": str(order.id),
            "metadata": {"order_id": order.id, "payment_id": payment.id},
            "payer": {"email": order.customer_email},
        }
        if order.customer_cpf:
            payload["payer"]["identification"] = {"type": "CPF", "number": "".join(filter(str.isdigit, order.customer_cpf))}
        if self.settings.MERCADO_PAGO_WEBHOOK_URL:
            payload["notification_url"] = self.settings.MERCADO_PAGO_WEBHOOK_URL

        expires_at = None
        if payment.metodo == PaymentMethod.PIX:
            expires_at = datetime.now(ZoneInfo("America/Sao_Paulo")) + timedelta(minutes=self.settings.MERCADO_PAGO_PIX_EXPIRATION_MINUTES)
            payload.update(payment_method_id="pix", date_of_expiration=expires_at.isoformat(timespec="milliseconds"))
        else:
            card_data = card_data or {}
            if any(not card_data.get(field) for field in ("token", "payment_method_id", "installments")):
                raise ValueError("Dados tokenizados do cartão são obrigatórios")
            payload.update(token=card_data["token"], payment_method_id=card_data["payment_method_id"], installments=int(card_data["installments"]))
            if card_data.get("issuer_id"):
                payload["issuer_id"] = card_data["issuer_id"]
            if card_data.get("payer_email"):
                payload["payer"]["email"] = card_data["payer_email"]
            if card_data.get("identification_number"):
                payload["payer"]["identification"] = {"type": card_data.get("identification_type") or "CPF", "number": card_data["identification_number"]}

        self.payment_repository.update(payment.id, {"gateway": "MERCADO_PAGO", "idempotency_key": idempotency_key, "status": PaymentStatus.PROCESSING.value, "expires_at": expires_at.replace(tzinfo=None) if expires_at else None})
        gateway_data = self.gateway.create_payment(payload, idempotency_key)
        transaction_data = ((gateway_data.get("point_of_interaction") or {}).get("transaction_data") or {})
        self.payment_repository.update(payment.id, {"codigo_transacao": str(gateway_data.get("id")), "pix_qr_code": transaction_data.get("qr_code"), "pix_qr_code_base64": transaction_data.get("qr_code_base64"), "pix_ticket_url": transaction_data.get("ticket_url")})
        return ReconcilePaymentUseCase(self.payment_repository, self.order_repository).execute(gateway_data)
