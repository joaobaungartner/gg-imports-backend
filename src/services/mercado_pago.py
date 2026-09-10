import hashlib
import hmac
from dataclasses import dataclass
from typing import Any

import httpx


class MercadoPagoError(ValueError):
    pass


@dataclass
class MercadoPagoGateway:
    access_token: str
    base_url: str = "https://api.mercadopago.com"
    timeout: float = 15.0

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        try:
            response = httpx.request(
                method,
                f"{self.base_url.rstrip('/')}{path}",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except httpx.RequestError as exc:
            raise MercadoPagoError("Mercado Pago indisponível. Tente novamente.") from exc
        if response.status_code >= 400:
            try:
                data = response.json()
                message = data.get("message") or data.get("error")
            except ValueError:
                message = None
            raise MercadoPagoError(message or "Mercado Pago recusou a operação")
        return response.json()

    def create_payment(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        return self._request("POST", "/v1/payments", payload=payload, idempotency_key=idempotency_key)

    def get_payment(self, gateway_payment_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/payments/{gateway_payment_id}")

    def refund(self, gateway_payment_id: str, idempotency_key: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/payments/{gateway_payment_id}/refunds",
            payload={},
            idempotency_key=idempotency_key,
        )


def verify_webhook_signature(
    *,
    secret: str,
    signature: str | None,
    request_id: str | None,
    data_id: str | None,
) -> bool:
    if not secret or not signature or not request_id or not data_id:
        return False
    parts = {}
    for item in signature.split(","):
        key, separator, value = item.strip().partition("=")
        if separator:
            parts[key] = value
    timestamp = parts.get("ts")
    received_hash = parts.get("v1")
    if not timestamp or not received_hash:
        return False
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{timestamp};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received_hash)
