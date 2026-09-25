from decimal import Decimal

import pytest

from src.entities.order import OrderEntity
from src.entities.order_item import OrderItemEntity
from src.repositories.order_repository import OrderRepository


@pytest.fixture
def order(commerce_api, db_session):
    value = OrderEntity(1, client_id=1, endereco_id=1, customer_name='Buyer',
        customer_email='buyer@example.com', shipping_method='ENTREGA',
        itens=[OrderItemEntity(1, 2, 100)])
    value.calcular_total()
    return OrderRepository(db_session).create(value)


@pytest.mark.parametrize('path', ['/orders/', '/orders/?status=PENDING_PAYMENT', '/orders/?client_id=1',
    '/orders/?status=PENDING_PAYMENT&client_id=1', '/orders/me', '/orders/client/1',
    '/orders/1', '/orders/1/total', '/admin/orders/', '/admin/orders/summary',
    '/admin/orders/1', '/admin/orders/1/history', '/order-items/1', '/order-items/order/1', '/order-items/1/subtotal'])
def test_order_reads(commerce_api, order, path):
    response = commerce_api.get(path)
    assert response.status_code == 200, response.text
    assert response.json()


@pytest.mark.parametrize('method,path,body,field,expected', [
    ('patch', '/orders/1/status', {'status': 'PAID'}, 'status', 'PAID'),
    ('patch', '/orders/1/cancel', None, 'status', 'CANCELED'),
    ('patch', '/orders/1/confirm', None, 'status', 'PAID'),
    ('post', '/orders/1/coupon', {'cupom_id': 1}, 'valor_total', '180.00'),
    ('patch', '/admin/orders/1/status', {'status': 'PAID', 'note': 'Reviewed'}, 'status', 'PAID'),
    ('patch', '/admin/orders/1/notes', {'admin_notes': 'Call buyer'}, 'admin_notes', 'Call buyer'),
    ('patch', '/admin/orders/1/tracking', {'codigo_rastreio': ' ABC123 ', 'url_rastreio': 'https://example.invalid/track'}, 'codigo_rastreio', 'ABC123'),
    ('patch', '/order-items/1/quantity', {'quantidade': 3}, 'quantidade', 3),
    ('delete', '/order-items/1', None, 'ativo', False),
])
def test_order_mutations(commerce_api, order, method, path, body, field, expected):
    response = commerce_api.request(method, path, json=body)
    assert response.status_code == 200, response.text
    assert response.json()[field] == expected


def test_add_and_remove_order_items(commerce_api, order):
    response = commerce_api.post('/orders/1/items', json={'product_id': 1, 'quantidade': 1})
    assert response.status_code == 200, response.text
    assert Decimal(response.json()['valor_total']) == 300
    item_id = response.json()['itens'][-1]['id']
    response = commerce_api.delete(f'/orders/1/items/{item_id}')
    assert response.status_code == 200
    assert Decimal(response.json()['valor_total']) == 200
    response = commerce_api.post('/order-items/', json={'order_id': 1, 'product_id': 1, 'quantidade': 1})
    assert response.status_code == 201, response.text


@pytest.mark.parametrize('path', ['/orders/999', '/admin/orders/999', '/admin/orders/999/history', '/order-items/999'])
def test_missing_order_resources(commerce_api, path):
    assert commerce_api.get(path).status_code == 404


def test_order_errors_and_tracking(commerce_api, order):
    assert commerce_api.patch('/orders/1/status', json={'status': 'DELIVERED'}).status_code == 400
    assert commerce_api.patch('/admin/orders/999/tracking', json={'codigo_rastreio': 'ABC'}).status_code == 404
    assert commerce_api.post('/orders/track', json={'order_id': 1, 'identifier': 'buyer@example.com'}).status_code == 200
    assert commerce_api.post('/orders/track', json={'order_id': 1, 'identifier': 'wrong'}).status_code == 404
    assert commerce_api.post('/orders/track', json={'order_id': -1, 'identifier': ''}).status_code == 422
    assert commerce_api.post('/admin/orders/expire-reservations').json() == {'expired_order_ids': [], 'count': 0}


@pytest.mark.parametrize('shipping,freight', [('RETIRADA', 0), ('ENTREGA', 34)])
def test_checkout_reserves_consolidated_items(commerce_api, db_session, shipping, freight):
    from src.models import ProductModel
    payload = dict(customer_name=' Buyer ', customer_email='buyer@example.com', customer_phone='11999998888',
        shipping_address=dict(cep='01001-000', street='Rua', number='1', neighborhood='Centro', city='SP', state='SP'),
        shipping_method=shipping, payment_method='PIX', frete=freight, coupon_code='SAVE10',
        items=[{'product_id': 1, 'quantity': 1}, {'product_id': 1, 'quantity': 2}])
    response = commerce_api.post('/orders/', json=payload)
    assert response.status_code == 201, response.text
    result = response.json()
    assert len(result['itens']) == 1 and result['itens'][0]['quantidade'] == 3
    assert Decimal(result['valor_total']) == Decimal(270 + freight)
    assert db_session.get(ProductModel, 1).estoque == 17
    stored = OrderRepository(db_session).get_by_id(result['id'])
    assert stored.estoque_reservado and stored.reserva_expira_em is not None
    assert commerce_api.patch(f"/orders/{result['id']}/cancel").status_code == 200
    assert commerce_api.patch(f"/orders/{result['id']}/cancel").status_code == 200
    assert db_session.get(ProductModel, 1).estoque == 20
