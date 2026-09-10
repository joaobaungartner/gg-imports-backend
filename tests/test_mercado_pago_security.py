import hashlib
import hmac

from src.services.mercado_pago import verify_webhook_signature


def test_validates_mercado_pago_webhook_signature():
    secret = "webhook-secret"
    timestamp = "1700000000"
    request_id = "request-123"
    data_id = "987654"
    manifest = f"id:{data_id};request-id:{request_id};ts:{timestamp};"
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()

    assert verify_webhook_signature(
        secret=secret,
        signature=f"ts={timestamp},v1={digest}",
        request_id=request_id,
        data_id=data_id,
    )


def test_rejects_invalid_mercado_pago_webhook_signature():
    assert not verify_webhook_signature(
        secret="webhook-secret",
        signature="ts=1700000000,v1=invalid",
        request_id="request-123",
        data_id="987654",
    )
