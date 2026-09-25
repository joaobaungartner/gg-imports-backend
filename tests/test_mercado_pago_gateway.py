import hashlib
import hmac
from unittest.mock import Mock

import httpx
import pytest

from src.services.mercado_pago import MercadoPagoError, MercadoPagoGateway, verify_webhook_signature


@pytest.mark.parametrize('operation,method,path,payload,key', [
    ('create_payment', 'POST', '/v1/payments', {'amount': 10}, 'create-key'),
    ('get_payment', 'GET', '/v1/payments/123', None, None),
    ('refund', 'POST', '/v1/payments/123/refunds', {}, 'refund-key'),
])
def test_gateway_requests(monkeypatch, operation, method, path, payload, key):
    response = {'id': 123, 'status': 'pending'}
    request = Mock(return_value=httpx.Response(200, json=response))
    monkeypatch.setattr(httpx, 'request', request)
    gateway = MercadoPagoGateway('fake-token', 'https://example.invalid/', 3)
    args = (payload, key) if operation == 'create_payment' else (('123', key) if key else ('123',))
    assert getattr(gateway, operation)(*args) == response
    headers = {'Authorization': 'Bearer fake-token'}
    if key:
        headers['X-Idempotency-Key'] = key
    request.assert_called_once_with(method, 'https://example.invalid' + path,
                                    headers=headers, json=payload, timeout=3)


@pytest.mark.parametrize('response,message', [
    (httpx.Response(400, json={'message': 'invalid payment', 'error': 'other'}), 'invalid payment'),
    (httpx.Response(401, json={'error': 'invalid token'}), 'invalid token'),
    (httpx.Response(500, text='bad gateway'), 'recusou'),
    (httpx.Response(400, json={}), 'recusou'),
])
def test_gateway_http_errors(monkeypatch, response, message):
    monkeypatch.setattr(httpx, 'request', Mock(return_value=response))
    with pytest.raises(MercadoPagoError, match=message):
        MercadoPagoGateway('fake').get_payment('123')


def test_gateway_network_error(monkeypatch):
    error = httpx.RequestError('offline')
    monkeypatch.setattr(httpx, 'request', Mock(side_effect=error))
    with pytest.raises(MercadoPagoError, match='indisponível') as caught:
        MercadoPagoGateway('fake').get_payment('123')
    assert caught.value.__cause__ is error


@pytest.mark.parametrize('field', ['secret', 'signature', 'request_id', 'data_id'])
def test_signature_requires_all_fields(field):
    args = dict(secret='secret', signature='ts=1,v1=hash', request_id='req', data_id='abc')
    args[field] = ''
    assert not verify_webhook_signature(**args)


@pytest.mark.parametrize('signature', ['v1=hash', 'ts=1', 'garbage,ts=1', 'ts=,v1=hash'])
def test_signature_requires_timestamp_and_digest(signature):
    assert not verify_webhook_signature(secret='secret', signature=signature, request_id='req', data_id='abc')


@pytest.mark.parametrize('data_id', ['abc', 'ABC', 'AbC'])
def test_signature_normalizes_data_id(data_id):
    digest = hmac.new(b'secret', b'id:abc;request-id:req;ts:1;', hashlib.sha256).hexdigest()
    assert verify_webhook_signature(secret='secret', signature=f'ignored, ts=1, v1={digest}',
                                    request_id='req', data_id=data_id)
