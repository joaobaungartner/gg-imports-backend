from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.entities.order import OrderStatus
from src.entities.payment import PaymentEntity, PaymentStatus
from src.use_cases.payment.confirm_payment import ConfirmPaymentUseCase
from src.use_cases.payment.reconcile_payment import ReconcilePaymentUseCase


@pytest.mark.parametrize('case,message', [('missing', 'local não encontrado'), ('reference', 'Referência'), ('amount', 'Valor recebido'), ('status', 'Status desconhecido')])
def test_reconcile_rejects_untrusted_gateway_data(case, message):
    payments, orders = Mock(), Mock()
    payment = PaymentEntity(1, 2, 'PIX', 100)
    payments.get_by_id.return_value = payment
    data = dict(id='mp-1', metadata={'payment_id': 1}, external_reference='2', transaction_amount=100, status='pending')
    if case == 'missing':
        payments.get_by_id.return_value = None
        payments.get_by_transaction_code.return_value = None
    if case == 'reference': data['external_reference'] = '3'
    if case == 'amount': data['transaction_amount'] = 99
    if case == 'status': data['status'] = 'unknown'
    with pytest.raises(ValueError, match=message): ReconcilePaymentUseCase(payments, orders).execute(data)
    payments.update.assert_not_called()
    orders.update_status.assert_not_called()


@pytest.mark.parametrize('status', [PaymentStatus.PAID, PaymentStatus.REFUNDED])
def test_reconcile_ignores_stale_pending_status(status):
    payments = Mock()
    payment = PaymentEntity(1, 2, 'PIX', 100, status=status)
    payments.get_by_transaction_code.return_value = payment
    payments.get_by_id.return_value = payment
    result = ReconcilePaymentUseCase(payments, Mock()).execute(
        dict(id='mp-1', external_reference='2', transaction_amount=100, status='pending'))
    assert result is payment
    payments.get_by_transaction_code.assert_called_once_with('mp-1')
    payments.update.assert_not_called()


def test_reconcile_cancellation_cancels_eligible_order(monkeypatch):
    payments, orders = Mock(), Mock()
    payments.get_by_id.return_value = PaymentEntity(1, 2, 'PIX', 100)
    orders.get_by_id.return_value = SimpleNamespace(status=OrderStatus.PENDING_PAYMENT)
    cancel = Mock()
    monkeypatch.setattr('src.use_cases.order.cancel_order.CancelOrderUseCase', Mock(return_value=cancel))
    result = ReconcilePaymentUseCase(payments, orders).execute(
        dict(id='mp-1', metadata={'payment_id': 1}, external_reference='2', transaction_amount=100, status='cancelled'))
    assert result is payments.update.return_value
    assert payments.update.call_args.args[1]['status'] == 'CANCELED'
    cancel.execute.assert_called_once_with(2)


@pytest.mark.parametrize('case,message', [('missing', 'Pagamento não encontrado'), ('order', 'Pedido não encontrado'), ('transaction', 'outra transação')])
def test_confirm_guards_roll_back(case, message):
    payments, orders = Mock(), Mock()
    payment = PaymentEntity(1, 2, 'PIX', 100, codigo_transacao='other' if case == 'transaction' else None)
    payments.get_by_id.return_value = None if case == 'missing' else payment
    payments.get_by_id_for_update.return_value = payment
    if case == 'order': orders.get_by_id_for_update.return_value = None
    with pytest.raises(ValueError, match=message): ConfirmPaymentUseCase(payments, orders).execute(1, 'mp-1')
    orders.db.rollback.assert_called_once()
    orders.db.commit.assert_not_called()
    payments.update.assert_not_called()
