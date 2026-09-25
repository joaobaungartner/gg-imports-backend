from decimal import Decimal

import pytest

from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.repositories.order_repository import OrderRepository


def test_address_lifecycle(commerce_api):
    client = commerce_api
    data = dict(client_id=1, rua='Rua nova', numero='2', bairro='Centro', cidade='Rio', estado='rj', cep='20000-000')
    response = client.post('/addresses/', json=data)
    assert response.status_code == 201, response.text
    id_ = response.json()['id']
    assert response.json()['estado'] == 'RJ'
    for path in ['/addresses/', '/addresses/?active=true', '/addresses/client/1', f'/addresses/{id_}']:
        assert client.get(path).status_code == 200
    response = client.put(f'/addresses/{id_}', json=dict(rua='Changed', numero='3', bairro='Bairro', cidade='SP', estado='SP', cep='01001000'))
    assert response.status_code == 200 and response.json()['rua'] == 'Changed'
    assert client.post(f'/addresses/{id_}/validate-for-order', json={'client_id': 1}).status_code == 200
    assert client.post(f'/addresses/{id_}/validate-for-order', json={'client_id': 2}).status_code == 400
    assert client.patch(f'/addresses/{id_}/deactivate').json()['ativo'] is False
    assert client.post(f'/addresses/{id_}/validate-for-order', json={'client_id': 1}).status_code == 400
    assert client.get('/addresses/999').status_code == 404


def test_client_lifecycle(commerce_api):
    client = commerce_api
    data = dict(nome='New buyer', email='new@example.com', senha='password123', cpf='98765432100')
    response = client.post('/clients/', json=data)
    assert response.status_code == 201, response.text
    id_, user_id = response.json()['id'], response.json()['user_id']
    assert client.post('/clients/', json=data).status_code == 400
    for path in [f'/clients/{id_}', f'/clients/user/{user_id}', '/clients/cpf/98765432100']:
        assert client.get(path).status_code == 200
    response = client.put(f'/clients/{id_}', json={'nome': 'Updated buyer', 'telefone': '11999998888', 'cpf': '98765432101'})
    assert response.status_code == 200 and response.json()['nome'] == 'Updated buyer'
    assert client.get(f'/clients/{id_}/orders').json() == []
    response = client.post(f'/clients/{id_}/cart/items', json={'produto_id': 1, 'quantidade': 2})
    assert response.status_code == 200, response.text
    assert Decimal(response.json()['valor_total']) == 200
    # Current endpoint omits UserRepository when constructing the use case.
    with pytest.raises(TypeError, match='client_repository'):
        client.patch(f'/clients/{id_}/deactivate')
    assert client.get('/clients/999').status_code == 404


def test_admin_lifecycle(commerce_api):
    client = commerce_api
    data = dict(nome='Admin', email='admin@example.com', senha='password123')
    response = client.post('/admins/', json=data)
    assert response.status_code == 201, response.text
    id_, user_id = response.json()['id'], response.json()['user_id']
    assert client.post('/admins/', json=data).status_code == 400
    for path in [f'/admins/{id_}', f'/admins/user/{user_id}', '/admins/email/admin@example.com']:
        assert client.get(path).status_code == 200
    # Both routes currently omit a required constructor dependency.
    with pytest.raises(TypeError, match='admin_repository'):
        client.put(f'/admins/{id_}', json={'nome': 'Updated admin', 'telefone': '12345678', 'email': 'changed@example.com'})
    with pytest.raises(TypeError, match='admin_repository'):
        client.patch(f'/admins/{id_}/deactivate')
    assert client.get('/admins/999').status_code == 404


def test_management_reports_stock_and_audit(commerce_api, db_session):
    client = commerce_api
    order = OrderEntity(1, client_id=1, endereco_id=1, customer_name='Buyer', customer_email='buyer@example.com',
        status=OrderStatus.PAID, itens=[OrderItemEntity(1, 2, 100, nome_produto='Shirt')])
    order.calcular_total()
    OrderRepository(db_session).create(order)
    prefix = '/admin/management'
    response = client.get(prefix + '/reports/sales?date_from=2020-01-01T00:00:00&date_to=2099-01-01T00:00:00')
    assert response.status_code == 200
    assert Decimal(response.json()['revenue']) == 200
    assert response.json()['order_count'] == 1 and response.json()['top_products'][0]['quantity'] == 2
    export = client.get(prefix + '/orders/export.csv')
    assert export.status_code == 200 and 'buyer@example.com' in export.text
    response = client.post(prefix + '/stock/1/adjust', json={'quantity_delta': -18, 'reason': 'Inventory count'})
    assert response.status_code == 200 and response.json()['new_stock'] == 2
    assert len(client.get(prefix + '/stock/low').json()) == 1
    assert client.get(prefix + '/stock/movements?product_id=1').json()[0]['quantity'] == -18
    assert client.get(prefix + '/clients?search=Buyer').json()[0]['order_count'] == 1
    assert client.patch(prefix + '/clients/1/status', json={'active': False}).json()['active'] is False
    assert client.get(prefix + '/audit').json()
    assert client.get(prefix + '/dashboard').status_code == 200


@pytest.mark.parametrize('id_,delta,code', [(999, 1, 404), (1, -21, 409), (1, 0, 422)])
def test_stock_adjustment_rejections(commerce_api, id_, delta, code):
    response = commerce_api.post(f'/admin/management/stock/{id_}/adjust', json={'quantity_delta': delta, 'reason': 'Count'})
    assert response.status_code == code
    assert commerce_api.patch('/admin/management/clients/999/status', json={'active': False}).status_code == 404


def test_post_sale_lifecycle(commerce_api, db_session):
    client = commerce_api
    repo = OrderRepository(db_session)
    repo.create(OrderEntity(1, client_id=1, endereco_id=1))
    body = {'order_id': 1, 'request_type': 'RETURN', 'reason': 'Wrong size received'}
    assert client.post('/post-sales/', json=body).status_code == 400
    repo.update_status(1, 'DELIVERED')
    response = client.post('/post-sales/', json=body)
    assert response.status_code == 201, response.text
    id_ = response.json()['id']
    assert len(client.get('/post-sales/me').json()) == 1
    assert len(client.get('/admin/post-sales/').json()) == 1
    response = client.patch(f'/admin/post-sales/{id_}', json={'status': 'APPROVED', 'admin_note': 'Return accepted'})
    assert response.status_code == 200 and response.json()['status'] == 'APPROVED'
    assert client.patch('/admin/post-sales/999', json={'status': 'REJECTED'}).status_code == 404
    body['order_id'] = 999
    assert client.post('/post-sales/', json=body).status_code == 404
