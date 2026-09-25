from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.entities.payment import PaymentEntity, PaymentStatus
from src.models.payment_model import PaymentModel
from src.repositories.payment_repository import PaymentRepository
from src.use_cases.payment.get_payment_by_id import GetPaymentByIdUseCase
from src.use_cases.payment.get_payment_by_order import GetPaymentByOrderUseCase
from src.use_cases.payment.list_payments import ListPaymentsUseCase


@pytest.fixture
def repository():
    engine = create_engine('sqlite://')
    PaymentModel.__table__.create(engine)
    with Session(engine) as db:
        yield PaymentRepository(db)
    engine.dispose()


def test_repository_roundtrip_and_queries(repository):
    r = repository
    payment = r.create(PaymentEntity(None, 2, 'PIX', Decimal('100'), codigo_transacao='mp-1'))
    assert payment.id is not None
    assert payment.valor == Decimal('100')
    assert r.get_by_order_id(2) == payment
    assert r.get_by_transaction_code('mp-1') == payment
    assert r.get_by_id_for_update(payment.id) == payment
    assert r.list_all() == [payment]
    assert r.list_by_status('PENDING') == [payment]
    assert r.list_by_status('PAID') == []
    assert GetPaymentByIdUseCase(r).execute(payment.id) == payment
    assert GetPaymentByOrderUseCase(r).execute(2) == payment
    assert ListPaymentsUseCase(r).execute(status='PENDING', metodo='PIX') == [payment]
    assert ListPaymentsUseCase(r).execute(metodo='CREDIT_CARD') == []
    assert ListPaymentsUseCase(r).execute() == [payment]


def test_repository_updates_and_delete(repository):
    r = repository
    r.create(PaymentEntity(7, 2, 'PIX', 100))
    assert r.update(7, {'status_detail': 'detail', 'unknown_field': 'ignored'}, commit=False).status_detail == 'detail'
    assert r.update_status(7, 'PROCESSING').status == PaymentStatus.PROCESSING
    paid = r.confirm(7, 'mp-1')
    assert paid.status == PaymentStatus.PAID
    assert paid.codigo_transacao == 'mp-1'
    assert paid.data_pagamento is not None
    assert r.cancel(7).status == PaymentStatus.CANCELED
    assert not r.deactivate(7).ativo
    assert r.delete(7)
    assert r.get_by_id(7) is None


def test_repository_missing_records(repository):
    r = repository
    assert r.get_by_id(999) is None
    assert r.get_by_order_id(999) is None
    assert r.get_by_transaction_code('missing') is None
    assert r.get_by_id_for_update(999) is None
    assert r.update(999, {'status': 'PAID'}) is None
    assert not r.delete(999)
    for cls in (GetPaymentByIdUseCase, GetPaymentByOrderUseCase):
        with pytest.raises(ValueError, match='não encontrado'): cls(r).execute(999)


@pytest.mark.parametrize('fields', [{'order_id': 0}, {'valor': 0}, {'valor': -1}, {'metodo': None}])
def test_entity_validates_required_fields(fields):
    args = dict(id=1, order_id=2, metodo='PIX', valor=10)
    args.update(fields)
    with pytest.raises(ValueError): PaymentEntity(**args)


def test_entity_payment_lifecycle():
    payment = PaymentEntity(1, 2, 'PIX', 10.5)
    assert payment.valor == Decimal('10.5')
    assert payment.esta_pendente()
    assert not payment.esta_pago()
    assert not payment.esta_cancelado()
    assert not payment.esta_recusado()
    payment.processar_pagamento()
    assert payment.status == PaymentStatus.PROCESSING
    with pytest.raises(ValueError): payment.processar_pagamento()
    payment.confirmar_pagamento('mp-1')
    timestamp = payment.data_pagamento
    payment.confirmar_pagamento('mp-1')
    assert payment.data_pagamento == timestamp
    assert payment.esta_pago()
    with pytest.raises(ValueError): payment.confirmar_pagamento('mp-2')
    with pytest.raises(ValueError): payment.cancelar_pagamento()
    payment.estornar_pagamento()
    assert payment.status == PaymentStatus.REFUNDED
    with pytest.raises(ValueError): payment.estornar_pagamento()


def test_entity_pending_confirmation_and_status_helpers():
    payment = PaymentEntity(1, 2, 'PIX', 10)
    with pytest.raises(ValueError): payment.confirmar_pagamento('')
    payment.confirmar_pagamento('mp-1')
    assert payment.esta_pago()
    payment = PaymentEntity(2, 2, 'PIX', 10)
    payment.cancelar_pagamento()
    assert payment.esta_cancelado()
    with pytest.raises(ValueError): payment.alterar_status('PAID')
    payment = PaymentEntity(3, 2, 'PIX', 10)
    payment.alterar_status('FAILED')
    assert payment.esta_recusado()
    code = payment.gerar_codigo_transacao()
    assert code.startswith('GG-') and len(code) == 15
    assert code[3:] == code[3:].upper()
    int(code[3:], 16)
