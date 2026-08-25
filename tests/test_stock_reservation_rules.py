from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.entities.payment import PaymentEntity, PaymentMethod, PaymentStatus
from src.use_cases.order.cancel_order import CancelOrderUseCase


class DbSpy:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def reserved_order():
    return OrderEntity(
        id=1,
        customer_name="Cliente",
        customer_email="cliente@example.com",
        customer_phone="11999999999",
        shipping_cep="01001000",
        shipping_street="Praça da Sé",
        shipping_number="1",
        shipping_neighborhood="Sé",
        shipping_city="São Paulo",
        shipping_state="SP",
        shipping_method="ENTREGA",
        payment_method="PIX",
        status=OrderStatus.PENDING_PAYMENT,
        estoque_reservado=True,
        itens=[
            OrderItemEntity(
                product_id=42,
                quantidade=2,
                preco_unitario=Decimal("100"),
            )
        ],
    )


def test_cancel_releases_reserved_stock_only_once():
    order = reserved_order()
    db = DbSpy()

    class OrderRepo:
        def __init__(self):
            self.db = db

        def get_by_id_for_update(self, order_id):
            return order

        def release_reservation(self, order_id):
            order.estoque_reservado = False
            order.reserva_expira_em = None

        def update_status(self, order_id, status, commit=False):
            order.status = OrderStatus(status)
            return order

        def get_by_id(self, order_id):
            return order

    released = []
    product_repo = SimpleNamespace(
        release_stock=lambda product_id, quantity: released.append(
            (product_id, quantity)
        )
    )
    history_repo = SimpleNamespace(create=lambda **kwargs: None)
    use_case = CancelOrderUseCase(OrderRepo(), history_repo, product_repo)

    assert use_case.execute(1).status == OrderStatus.CANCELED
    assert use_case.execute(1).status == OrderStatus.CANCELED
    assert released == [(42, 2)]
    assert db.commits == 1


def test_payment_confirmation_is_idempotent_for_same_transaction():
    payment = PaymentEntity(
        id=1,
        order_id=1,
        metodo=PaymentMethod.PIX,
        valor=Decimal("100"),
        status=PaymentStatus.PAID,
        codigo_transacao="PIX-123",
    )

    payment.confirmar_pagamento("PIX-123")
    assert payment.status == PaymentStatus.PAID

    with pytest.raises(ValueError, match="outra transação"):
        payment.confirmar_pagamento("PIX-OUTRA")
