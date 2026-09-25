from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock
import uuid

import pytest

from src.entities.order import OrderStatus
from src.entities.payment import PaymentEntity, PaymentMethod, PaymentStatus
from src.use_cases.payment.create_payment import CreatePaymentUseCase
from src.use_cases.payment.cancel_payment import CancelPaymentUseCase
from src.use_cases.payment.update_payment_status import UpdatePaymentStatusUseCase
from src.use_cases.payment import process_payment, refund_payment


@pytest.fixture
def context(monkeypatch):
    payment = PaymentEntity(1, 2, 'PIX', Decimal('100'))
    order = SimpleNamespace(id=2, ativo=True, valor_total=Decimal('100'),
                            status=OrderStatus.PENDING_PAYMENT, customer_email='buyer@example.com',
                            customer_cpf='123.456.789-00')
    payments, orders, gateway = Mock(), Mock(), Mock()
    payments.get_by_id.return_value = payment
    payments.get_by_id_for_update.return_value = payment
    payments.get_by_order_id.return_value = None
    orders.get_by_id.return_value = order
    settings = SimpleNamespace(MERCADO_PAGO_ACCESS_TOKEN='fake', MERCADO_PAGO_API_BASE_URL='https://example.invalid',
                               MERCADO_PAGO_WEBHOOK_URL='https://example.invalid/webhook', MERCADO_PAGO_PIX_EXPIRATION_MINUTES=30)
    for module in (process_payment, refund_payment):
        monkeypatch.setattr(module, 'get_settings', lambda: settings)
    return SimpleNamespace(payment=payment, order=order, payments=payments, orders=orders, gateway=gateway, settings=settings)


@pytest.mark.parametrize('case,message', [('missing', 'Pedido'), ('inactive', 'Pedido'),
    ('existing', 'já possui'), ('zero', 'Valor'), ('negative', 'Valor'), ('method', 'Método')])
def test_create_rejects_invalid_payment(context, case, message):
    c = context
    if case == 'missing': c.orders.get_by_id.return_value = None
    if case == 'inactive': c.order.ativo = False
    if case == 'existing': c.payments.get_by_order_id.return_value = c.payment
    if case in ('zero', 'negative'): c.order.valor_total = Decimal('0' if case == 'zero' else '-1')
    with pytest.raises(ValueError, match=message):
        CreatePaymentUseCase(c.orders, c.payments).execute(2, 'INVALID' if case == 'method' else 'PIX')
    c.payments.create.assert_not_called()


@pytest.mark.parametrize('method,expected', [('PIX', PaymentMethod.PIX), ('CARTAO', PaymentMethod.CREDIT_CARD), ('CREDIT_CARD', PaymentMethod.CREDIT_CARD)])
def test_create_uses_order_total(context, method, expected):
    c = context
    c.payments.get_by_order_id.return_value = SimpleNamespace(ativo=False)
    c.payments.create.side_effect = lambda payment: payment
    result = CreatePaymentUseCase(c.orders, c.payments).execute(2, method, valor=1)
    assert (result.order_id, result.valor, result.metodo, result.status) == (2, Decimal('100'), expected, PaymentStatus.PENDING)


@pytest.mark.parametrize('use_case,args,status', [(CancelPaymentUseCase, (), 'CANCELED'), (UpdatePaymentStatusUseCase, ('PROCESSING',), 'PROCESSING')])
@pytest.mark.parametrize('case', ['missing', 'updated_missing', 'success'])
def test_status_changes(context, use_case, args, status, case):
    c = context
    if case == 'missing': c.payments.get_by_id.return_value = None
    if case == 'updated_missing': c.payments.update_status.return_value = None
    if case == 'success':
        assert use_case(c.payments).execute(1, *args) is c.payments.update_status.return_value
    else:
        with pytest.raises(ValueError, match='não encontrado'):
            use_case(c.payments).execute(1, *args)
    if case == 'missing': c.payments.update_status.assert_not_called()
    else: c.payments.update_status.assert_called_once_with(1, status)


def test_update_invalid_status(context):
    with pytest.raises(ValueError, match='Status de pagamento inválido'):
        UpdatePaymentStatusUseCase(context.payments).execute(1, 'invalid')
    context.payments.update_status.assert_not_called()


@pytest.mark.parametrize('module,cls', [(process_payment, process_payment.ProcessPaymentUseCase), (refund_payment, refund_payment.RefundPaymentUseCase)])
def test_gateway_configuration(context, monkeypatch, module, cls):
    c = context
    factory = Mock(return_value=c.gateway)
    monkeypatch.setattr(module, 'MercadoPagoGateway', factory)
    assert cls(c.payments, c.orders).gateway is c.gateway
    factory.assert_called_once_with('fake', 'https://example.invalid')
    c.settings.MERCADO_PAGO_ACCESS_TOKEN = ''
    with pytest.raises(ValueError, match='não configurado'):
        cls(c.payments, c.orders)


@pytest.mark.parametrize('case', ['missing', 'pending', 'no_transaction', 'refunded'])
def test_refund_guards(context, case):
    c = context
    c.payment.status = PaymentStatus.PAID
    if case == 'missing': c.payments.get_by_id.return_value = None
    if case == 'pending': c.payment.status = PaymentStatus.PENDING
    if case == 'refunded': c.payment.status = PaymentStatus.REFUNDED
    use_case = refund_payment.RefundPaymentUseCase(c.payments, c.orders, c.gateway)
    if case == 'refunded': assert use_case.execute(1) is c.payment
    else:
        with pytest.raises(ValueError): use_case.execute(1)
    c.gateway.refund.assert_not_called()


def test_refund_retries_with_stable_key(context, monkeypatch):
    c = context
    c.payment.status, c.payment.codigo_transacao = PaymentStatus.PAID, 'mp-1'
    reconcile = Mock()
    monkeypatch.setattr(refund_payment, 'ReconcilePaymentUseCase', Mock(return_value=reconcile))
    c.gateway.get_payment.side_effect = [{'status': 'approved'}, {'status': 'refunded'}]
    use_case = refund_payment.RefundPaymentUseCase(c.payments, c.orders, c.gateway)
    with pytest.raises(RuntimeError, match='ainda não confirmado'): use_case.execute(1)
    reconcile.execute.assert_not_called()
    assert use_case.execute(1) is reconcile.execute.return_value
    expected = str(uuid.uuid5(uuid.NAMESPACE_URL, 'gg-imports:refund:1:mp-1'))
    assert c.gateway.refund.call_count == 2
    assert all(call.args == ('mp-1', expected) for call in c.gateway.refund.call_args_list)
    reconcile.execute.assert_called_once_with({'status': 'refunded'})


@pytest.mark.parametrize('case', ['missing', 'paid', 'order_missing', 'inactive', 'order_paid'])
def test_process_guards(context, case):
    c = context
    if case == 'missing': c.payments.get_by_id_for_update.return_value = None
    if case == 'paid': c.payment.status = PaymentStatus.PAID
    if case == 'order_missing': c.orders.get_by_id.return_value = None
    if case == 'inactive': c.order.ativo = False
    if case == 'order_paid': c.order.status = OrderStatus.PAID
    use_case = process_payment.ProcessPaymentUseCase(c.payments, c.orders, c.gateway)
    if case == 'paid': assert use_case.execute(1) is c.payment
    else:
        with pytest.raises(ValueError): use_case.execute(1)
    c.gateway.create_payment.assert_not_called()
    c.payments.update.assert_not_called()


@pytest.mark.parametrize('status', [PaymentStatus.PENDING, PaymentStatus.PROCESSING])
def test_process_reuses_existing_transaction(context, monkeypatch, status):
    c = context
    c.payment.status, c.payment.codigo_transacao = status, 'mp-1'
    reconcile = Mock()
    monkeypatch.setattr(process_payment, 'ReconcilePaymentUseCase', Mock(return_value=reconcile))
    assert process_payment.ProcessPaymentUseCase(c.payments, c.orders, c.gateway).execute(1) is reconcile.execute.return_value
    c.gateway.get_payment.assert_called_once_with('mp-1')
    reconcile.execute.assert_called_once_with(c.gateway.get_payment.return_value)
    c.gateway.create_payment.assert_not_called()


@pytest.mark.parametrize('missing', ['token', 'payment_method_id', 'installments', 'all'])
def test_process_requires_card_fields(context, missing):
    c = context
    c.payment.metodo = PaymentMethod.CREDIT_CARD
    data = dict(token='token', payment_method_id='visa', installments=1)
    if missing == 'all': data = None
    else: del data[missing]
    with pytest.raises(ValueError, match='tokenizados'):
        process_payment.ProcessPaymentUseCase(c.payments, c.orders, c.gateway).execute(1, data)
    c.gateway.create_payment.assert_not_called()
    c.payments.update.assert_not_called()


@pytest.mark.parametrize('method,status,key', [('PIX', PaymentStatus.PENDING, None), ('PIX', PaymentStatus.PENDING, 'existing'),
    ('PIX', PaymentStatus.FAILED, 'old'), ('CREDIT_CARD', PaymentStatus.PENDING, 'existing')])
def test_process_payload_and_gateway_fields(context, monkeypatch, method, status, key):
    c = context
    c.payment.metodo, c.payment.status, c.payment.idempotency_key = PaymentMethod(method), status, key
    monkeypatch.setattr(process_payment.uuid, 'uuid4', lambda: 'new-key')
    reconcile = Mock()
    monkeypatch.setattr(process_payment, 'ReconcilePaymentUseCase', Mock(return_value=reconcile))
    c.gateway.create_payment.return_value = {'id': 123, 'point_of_interaction': {'transaction_data': {
        'qr_code': 'qr', 'qr_code_base64': 'base64', 'ticket_url': 'ticket'}}}
    data = dict(token='token', payment_method_id='visa', installments='2', issuer_id='issuer',
                payer_email='custom@example.com', identification_number='999', identification_type='CPF')
    assert process_payment.ProcessPaymentUseCase(c.payments, c.orders, c.gateway).execute(1, data) is reconcile.execute.return_value
    payload, actual_key = c.gateway.create_payment.call_args.args
    assert actual_key == ('new-key' if status == PaymentStatus.FAILED or key is None else key)
    assert payload['transaction_amount'] == 100
    assert payload['external_reference'] == '2'
    assert payload['metadata'] == {'order_id': 2, 'payment_id': 1}
    assert payload['notification_url'] == c.settings.MERCADO_PAGO_WEBHOOK_URL
    if method == 'PIX':
        assert payload['payment_method_id'] == 'pix'
        assert payload['payer'] == {'email': 'buyer@example.com', 'identification': {'type': 'CPF', 'number': '12345678900'}}
        assert payload['date_of_expiration'].endswith('-03:00')
    else:
        assert (payload['token'], payload['installments'], payload['issuer_id']) == ('token', 2, 'issuer')
        assert payload['payer'] == {'email': 'custom@example.com', 'identification': {'type': 'CPF', 'number': '999'}}
    updates = c.payments.update.call_args_list
    assert updates[0].args[1]['idempotency_key'] == actual_key
    assert updates[0].args[1]['status'] == 'PROCESSING'
    assert updates[1].args == (1, {'codigo_transacao': '123', 'pix_qr_code': 'qr', 'pix_qr_code_base64': 'base64', 'pix_ticket_url': 'ticket'})
    reconcile.execute.assert_called_once_with(c.gateway.create_payment.return_value)
