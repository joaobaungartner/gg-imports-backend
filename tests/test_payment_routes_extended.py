import hashlib
import hmac
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.database.database import get_db
from src.routes import payment_routes as routes
from src.use_cases.payment.confirm_payment import LatePaymentRefundPending
from src.entities.payment import PaymentEntity


@pytest.fixture
def context(monkeypatch):
    settings = SimpleNamespace(MERCADO_PAGO_WEBHOOK_SECRET='secret', MERCADO_PAGO_ACCESS_TOKEN='fake',
                               MERCADO_PAGO_API_BASE_URL='https://example.invalid')
    gateway, reconcile, payments = Mock(), Mock(), Mock()
    monkeypatch.setattr(routes, 'get_settings', lambda: settings)
    monkeypatch.setattr(routes, 'MercadoPagoGateway', Mock(return_value=gateway))
    monkeypatch.setattr(routes, 'ReconcilePaymentUseCase', Mock(return_value=reconcile))
    monkeypatch.setattr(routes, 'PaymentRepository', Mock(return_value=payments))
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[get_db] = lambda: Mock()
    app.dependency_overrides[routes.get_current_admin] = lambda: SimpleNamespace(id=1)
    digest = hmac.new(b'secret', b'id:mp-1;request-id:req;ts:1;', hashlib.sha256).hexdigest()
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, settings=settings, gateway=gateway, reconcile=reconcile,
                              payments=payments, headers={'x-signature': f'ts=1,v1={digest}', 'x-request-id': 'req'})


@pytest.mark.parametrize('body', [True, False])
def test_valid_webhook(context, body):
    c = context
    url = '/payments/webhooks/mercado-pago' + ('' if body else '?data.id=mp-1')
    response = c.client.post(url, headers=c.headers, json={'data': {'id': 'mp-1'}})
    assert response.status_code == 200
    assert response.json() == {'received': True}
    c.gateway.get_payment.assert_called_once_with('mp-1')
    c.reconcile.execute.assert_called_once_with(c.gateway.get_payment.return_value)


@pytest.mark.parametrize('case,code', [('signature', 401), ('missing_id', 401), ('token', 503), ('late', 503), ('value', 422)])
def test_webhook_errors(context, case, code):
    c = context
    if case == 'signature': c.headers['x-signature'] = 'ts=1,v1=invalid'
    if case == 'token': c.settings.MERCADO_PAGO_ACCESS_TOKEN = ''
    if case == 'late': c.reconcile.execute.side_effect = LatePaymentRefundPending('retry refund')
    if case == 'value': c.reconcile.execute.side_effect = ValueError('invalid payment')
    response = c.client.post('/payments/webhooks/mercado-pago', headers=c.headers,
                             json={} if case == 'missing_id' else {'data': {'id': 'mp-1'}})
    assert response.status_code == code
    if case in ('signature', 'missing_id', 'token'):
        c.gateway.get_payment.assert_not_called()
        c.reconcile.execute.assert_not_called()
    else:
        assert response.json()['detail'] == ('retry refund' if case == 'late' else 'invalid payment')


@pytest.mark.parametrize('case', ['missing', 'no_transaction', 'token'])
def test_reconcile_guards(context, case):
    c = context
    c.payments.get_by_id.return_value = None if case == 'missing' else SimpleNamespace(codigo_transacao=None if case == 'no_transaction' else 'mp-1')
    if case == 'token': c.settings.MERCADO_PAGO_ACCESS_TOKEN = ''
    response = c.client.post('/payments/1/reconcile')
    assert response.status_code == 400
    assert response.json()['detail'] == ('Mercado Pago não configurado' if case == 'token' else 'Pagamento ainda não enviado ao Mercado Pago')
    c.gateway.get_payment.assert_not_called()


@pytest.mark.parametrize('method,path,body,case,expected_args', [
    ('post', '/payments/', {'order_id': 2, 'metodo': 'PIX'}, 'CreatePaymentUseCase', (2, 'PIX')),
    ('get', '/payments/order/2', None, 'GetPaymentByOrderUseCase', (2,)),
    ('get', '/payments/1', None, 'GetPaymentByIdUseCase', (1,)),
    ('post', '/payments/1/process', None, 'ProcessPaymentUseCase', (1, None)),
    ('post', '/payments/1/process', {'token': 'token'}, 'ProcessPaymentUseCase', (1, {'token': 'token'})),
    ('post', '/payments/1/cancel', None, 'CancelPaymentUseCase', (1,)),
    ('post', '/payments/1/refund', None, 'RefundPaymentUseCase', (1,)),
    ('patch', '/payments/1/status', {'status': 'PROCESSING'}, 'UpdatePaymentStatusUseCase', (1, 'PROCESSING')),
])
def test_payment_endpoints_delegate_and_serialize(context, monkeypatch, method, path, body, case, expected_args):
    c = context
    payment = PaymentEntity(1, 2, 'PIX', 100)
    use_case = Mock()
    use_case.execute.return_value = payment
    monkeypatch.setattr(routes, case, Mock(return_value=use_case))
    for guard in ('ensure_order_owner_or_admin', 'ensure_payment_access_by_order', 'ensure_payment_owner_or_admin'):
        monkeypatch.setattr(routes, guard, Mock())
    c.client.app.dependency_overrides[routes.get_current_user] = lambda: SimpleNamespace(id=1)
    response = c.client.request(method, path, json=body)
    assert response.status_code == (201 if case == 'CreatePaymentUseCase' else 200)
    assert response.json()['id'] == 1
    assert response.json()['metodo'] == 'PIX'
    use_case.execute.assert_called_once_with(*expected_args)


def test_list_payments_filters_and_serializes(context, monkeypatch):
    use_case = Mock()
    use_case.execute.return_value = [PaymentEntity(1, 2, 'PIX', 100)]
    monkeypatch.setattr(routes, 'ListPaymentsUseCase', Mock(return_value=use_case))
    response = context.client.get('/payments/?status=PENDING&metodo=PIX')
    assert response.status_code == 200
    assert response.json()[0]['id'] == 1
    use_case.execute.assert_called_once_with(status='PENDING', metodo='PIX')


def test_reconcile_success(context):
    c = context
    c.payments.get_by_id.return_value = PaymentEntity(1, 2, 'PIX', 100, codigo_transacao='mp-1')
    c.reconcile.execute.return_value = c.payments.get_by_id.return_value
    response = c.client.post('/payments/1/reconcile')
    assert response.status_code == 200
    assert response.json()['codigo_transacao'] == 'mp-1'
    c.gateway.get_payment.assert_called_once_with('mp-1')
    c.reconcile.execute.assert_called_once_with(c.gateway.get_payment.return_value)
