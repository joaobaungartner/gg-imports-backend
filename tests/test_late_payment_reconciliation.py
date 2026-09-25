from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.database.database import Base
from src.models import CategoryModel, ProductModel, OrderModel, OrderItemModel, PaymentModel
from src.models.notification_model import NotificationModel
from src.models.stock_movement_model import StockMovementModel
from src.repositories.order_repository import OrderRepository
from src.repositories.payment_repository import PaymentRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.order_status_history_repository import OrderStatusHistoryRepository
from src.use_cases.order.expire_stock_reservations import ExpireStockReservationsUseCase
from src.use_cases.payment.confirm_payment import LatePaymentRefundPending, LATE_REFUND_PENDING
from src.use_cases.payment.reconcile_payment import ReconcilePaymentUseCase
from src.entities.order import OrderStatus
from src.entities.payment import PaymentStatus


def gateway_data(status="approved"):
    return {"id": "mp-1", "metadata": {"payment_id": 1}, "external_reference": "1",
            "transaction_amount": 100, "status": status, "status_detail": "accredited"}


@pytest.fixture
def context():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(CategoryModel(id=1, nome="Camisas"))
        db.add(ProductModel(id=1, category_id=1, nome="Camisa", preco=100,
                            tamanho="M", clube="Clube", tipo="Torcedor", estoque=0))
        db.add(OrderModel(id=1, customer_name="Cliente", customer_email="c@example.com",
                          shipping_cep="01001000", shipping_street="Rua", shipping_number="1",
                          shipping_neighborhood="Centro", shipping_city="São Paulo", shipping_state="SP",
                          status="PENDING_PAYMENT", estoque_reservado=True,
                          reserva_expira_em=datetime.utcnow() + timedelta(minutes=10), valor_total=100))
        db.add(OrderItemModel(order_id=1, product_id=1, quantidade=1, preco_unitario=100))
        db.add(PaymentModel(id=1, order_id=1, metodo="PIX", valor=100, status="PROCESSING",
                            codigo_transacao="mp-1"))
        db.commit()
        gateway = Mock()
        gateway.get_payment.return_value = gateway_data("refunded")
        yield db, gateway, ReconcilePaymentUseCase(PaymentRepository(db), OrderRepository(db), gateway)
    engine.dispose()


def expire(db):
    db.get(OrderModel, 1).reserva_expira_em = datetime.utcnow() - timedelta(minutes=1)
    db.commit()
    return ExpireStockReservationsUseCase(OrderRepository(db), ProductRepository(db), OrderStatusHistoryRepository(db)).execute()


def test_expired_order_is_refunded_without_reserving_or_releasing_stock_twice(context):
    db, gateway, reconcile = context
    assert expire(db) == [1]
    assert reconcile.execute(gateway_data()).status == PaymentStatus.REFUNDED
    assert OrderRepository(db).get_by_id(1).status == OrderStatus.CANCELED
    assert db.get(ProductModel, 1).estoque == 1
    assert db.query(StockMovementModel).count() == 1
    assert db.query(NotificationModel).filter_by(event="PAYMENT_APPROVED").count() == 0
    assert reconcile.execute(gateway_data()).status == PaymentStatus.REFUNDED
    gateway.refund.assert_called_once()


def test_approval_after_deadline_before_expiration_job_also_refunds(context):
    db, gateway, reconcile = context
    db.get(OrderModel, 1).reserva_expira_em = datetime.utcnow() - timedelta(seconds=1)
    db.commit()
    result = reconcile.execute(gateway_data())
    assert result.status == PaymentStatus.REFUNDED
    assert result.refunded_amount == Decimal("100")
    assert db.get(ProductModel, 1).estoque == 1
    assert OrderRepository(db).get_by_id(1).status == OrderStatus.CANCELED


def test_failed_refund_is_durable_and_retry_uses_same_idempotency_key(context):
    db, gateway, reconcile = context
    expire(db)
    gateway.refund.side_effect = [ValueError("timeout"), {}]
    with pytest.raises(LatePaymentRefundPending):
        reconcile.execute(gateway_data())
    payment = PaymentRepository(db).get_by_id(1)
    assert payment.status == PaymentStatus.PAID
    assert payment.status_detail == LATE_REFUND_PENDING
    assert OrderRepository(db).get_by_id(1).status == OrderStatus.CANCELED
    assert reconcile.execute(gateway_data()).status == PaymentStatus.REFUNDED
    assert gateway.refund.call_args_list[0] == gateway.refund.call_args_list[1]
    assert db.query(NotificationModel).filter_by(event="LATE_PAYMENT_REFUND_PENDING").count() == 1


def test_refund_is_not_reported_as_complete_until_gateway_confirms(context):
    db, gateway, reconcile = context
    expire(db)
    gateway.get_payment.return_value = gateway_data("approved")
    with pytest.raises(LatePaymentRefundPending):
        reconcile.execute(gateway_data())
    assert PaymentRepository(db).get_by_id(1).status_detail == LATE_REFUND_PENDING
    assert gateway.refund.call_count == 1  # No recursive approval/refund loop.


def test_valid_approval_stays_paid_and_duplicate_is_idempotent(context):
    db, gateway, reconcile = context
    assert reconcile.execute(gateway_data()).status == PaymentStatus.PAID
    assert reconcile.execute(gateway_data()).status == PaymentStatus.PAID
    assert OrderRepository(db).get_by_id(1).status == OrderStatus.PAID
    assert db.get(ProductModel, 1).estoque == 0
    assert db.query(NotificationModel).filter_by(event="PAYMENT_APPROVED").count() == 1
    gateway.refund.assert_not_called()


def test_stale_expiration_scan_does_not_cancel_an_order_already_paid(context, monkeypatch):
    db, gateway, reconcile = context
    reconcile.execute(gateway_data())
    orders = OrderRepository(db)
    monkeypatch.setattr(orders, "list_expired_reservations", lambda now: [1])
    result = ExpireStockReservationsUseCase(orders, ProductRepository(db), OrderStatusHistoryRepository(db)).execute()
    assert result == []
    assert orders.get_by_id(1).status == OrderStatus.PAID
    assert db.get(ProductModel, 1).estoque == 0


def test_order_payment_and_notification_are_atomic(context, monkeypatch):
    db, gateway, reconcile = context
    def fail(*args, **kwargs):
        raise RuntimeError("database failure")
    monkeypatch.setattr("src.services.notification_service.NotificationService.email", fail)
    with pytest.raises(RuntimeError, match="database failure"):
        reconcile.execute(gateway_data())
    assert PaymentRepository(db).get_by_id(1).status == PaymentStatus.PROCESSING
    assert OrderRepository(db).get_by_id(1).status == OrderStatus.PENDING_PAYMENT


def test_refunded_payment_ignores_out_of_order_approval(context):
    db, gateway, reconcile = context
    expire(db)
    reconcile.execute(gateway_data("refunded"))
    assert reconcile.execute(gateway_data()).status == PaymentStatus.REFUNDED
    gateway.refund.assert_not_called()


def test_webhook_returns_retryable_error_when_refund_fails(context, monkeypatch):
    from types import SimpleNamespace
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.database.database import get_db
    from src.routes import payment_routes

    db, gateway, _ = context
    expire(db)
    gateway.get_payment.return_value = gateway_data()
    gateway.refund.side_effect = ValueError("gateway unavailable")
    monkeypatch.setattr(payment_routes, "verify_webhook_signature", lambda **kwargs: True)
    monkeypatch.setattr(payment_routes, "get_settings", lambda: SimpleNamespace(
        MERCADO_PAGO_WEBHOOK_SECRET="test", MERCADO_PAGO_ACCESS_TOKEN="test",
        MERCADO_PAGO_API_BASE_URL="https://example.invalid"))
    monkeypatch.setattr(payment_routes, "MercadoPagoGateway", lambda *args: gateway)
    app = FastAPI()
    app.include_router(payment_routes.router)
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        response = client.post("/payments/webhooks/mercado-pago?data.id=mp-1")
    assert response.status_code == 503
    assert PaymentRepository(db).get_by_id(1).status_detail == LATE_REFUND_PENDING


def test_late_approval_after_local_payment_cancellation_can_be_refunded(context):
    db, gateway, reconcile = context
    expire(db)
    db.get(PaymentModel, 1).status = "CANCELED"
    db.commit()
    assert reconcile.execute(gateway_data()).status == PaymentStatus.REFUNDED
    gateway.refund.assert_called_once()


def test_wrong_amount_never_triggers_refund(context):
    db, gateway, reconcile = context
    expire(db)
    data = gateway_data()
    data["transaction_amount"] = 99
    with pytest.raises(ValueError, match="Valor recebido"):
        reconcile.execute(data)
    gateway.refund.assert_not_called()
