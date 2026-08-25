"""Testes de regras de status e autorização administrativa de pedidos."""

from decimal import Decimal

import pytest

from src.entities.order import OrderEntity, OrderStatus


def _make_order(**kwargs) -> OrderEntity:
    defaults = {
        "id": 1,
        "customer_name": "Cliente Teste",
        "customer_email": "cliente@teste.com",
        "customer_phone": "11999999999",
        "shipping_cep": "01310100",
        "shipping_street": "Av Paulista",
        "shipping_number": "1000",
        "shipping_neighborhood": "Bela Vista",
        "shipping_city": "São Paulo",
        "shipping_state": "SP",
        "shipping_method": "ENTREGA",
        "payment_method": "PIX",
        "status": OrderStatus.PENDING_PAYMENT,
        "subtotal": Decimal("100"),
        "frete": Decimal("20"),
        "valor_total": Decimal("120"),
    }
    defaults.update(kwargs)
    return OrderEntity(**defaults)


def test_valid_transition_pending_to_paid():
    order = _make_order()
    order.alterar_status(OrderStatus.PAID)
    assert order.status == OrderStatus.PAID


def test_invalid_transition_pending_to_shipped():
    order = _make_order()
    with pytest.raises(ValueError, match="Transição de status inválida"):
        order.alterar_status(OrderStatus.SHIPPED)


def test_entrega_cannot_be_ready_for_pickup():
    order = _make_order(status=OrderStatus.PREPARING, shipping_method="ENTREGA")
    with pytest.raises(ValueError, match="pronto para retirada"):
        order.alterar_status(OrderStatus.READY_FOR_PICKUP)


def test_retirada_cannot_be_shipped():
    order = _make_order(status=OrderStatus.PREPARING, shipping_method="RETIRADA")
    with pytest.raises(ValueError, match="enviado"):
        order.alterar_status(OrderStatus.SHIPPED)


def test_delivered_requires_force():
    order = _make_order(status=OrderStatus.DELIVERED)
    with pytest.raises(ValueError, match="Transição de status inválida"):
        order.alterar_status(OrderStatus.PREPARING)
    order.alterar_status(OrderStatus.PREPARING, force=True)
    assert order.status == OrderStatus.PREPARING


def test_canceled_requires_force():
    order = _make_order(status=OrderStatus.CANCELED)
    with pytest.raises(ValueError, match="Transição de status inválida"):
        order.alterar_status(OrderStatus.PENDING_PAYMENT)
    order.alterar_status(OrderStatus.PENDING_PAYMENT, force=True)
    assert order.status == OrderStatus.PENDING_PAYMENT


def test_allowed_transitions_for_retirada_exclude_shipped():
    order = _make_order(status=OrderStatus.PREPARING, shipping_method="RETIRADA")
    allowed = order.allowed_transitions()
    assert OrderStatus.READY_FOR_PICKUP in allowed
    assert OrderStatus.SHIPPED not in allowed


def test_allowed_transitions_for_entrega_exclude_pickup():
    order = _make_order(status=OrderStatus.PREPARING, shipping_method="ENTREGA")
    allowed = order.allowed_transitions()
    assert OrderStatus.SHIPPED in allowed
    assert OrderStatus.READY_FOR_PICKUP not in allowed
