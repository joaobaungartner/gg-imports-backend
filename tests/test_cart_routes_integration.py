from decimal import Decimal

import pytest


def test_cart_lifecycle_and_duplicate_items(commerce_api):
    client = commerce_api
    created = client.post('/carts/', json={'client_id': 1})
    assert created.status_code == 201, created.text
    id_ = created.json()['id']
    for path in [f'/carts/{id_}', '/carts/client/1', '/carts/me/current']:
        assert client.get(path).json()['id'] == id_
    for _ in range(2):
        response = client.post(f'/carts/{id_}/items', json={'product_id': 1, 'quantidade': 2})
        assert response.status_code == 200, response.text
    items = response.json()['itens']
    assert len(items) == 1 and items[0]['quantidade'] == 4
    item_id = items[0]['id']
    assert Decimal(client.get(f'/carts/{id_}/total').json()['total']) == 400
    response = client.patch(f'/carts/items/{item_id}', json={'quantidade': 3})
    assert response.status_code == 200
    assert Decimal(response.json()['valor_total']) == 300
    response = client.post(f'/carts/{id_}/checkout/prepare')
    assert response.status_code == 200 and response.json()['valido_para_checkout']
    assert client.delete(f'/carts/items/{item_id}').status_code == 200
    assert Decimal(client.get(f'/carts/{id_}/total').json()['total']) == 0
    assert client.delete(f'/carts/{id_}/items').status_code == 200
    assert client.patch(f'/carts/{id_}/deactivate').json()['ativo'] is False
    # Existing behavior attempts a second cart despite the unique client_id.
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError, match='UNIQUE'):
        client.get('/carts/client/1')


def test_cart_item_lifecycle(commerce_api):
    client = commerce_api
    cart_id = client.get('/carts/me/current').json()['id']
    response = client.post('/cart-items/', json={'cart_id': cart_id, 'product_id': 1, 'quantidade': 2})
    assert response.status_code == 201, response.text
    id_ = response.json()['id']
    assert client.get(f'/cart-items/{id_}').json()['quantidade'] == 2
    assert len(client.get(f'/cart-items/cart/{cart_id}').json()) == 1
    assert Decimal(client.get(f'/cart-items/{id_}/subtotal').json()['subtotal']) == 200
    assert client.patch(f'/cart-items/{id_}/quantity', json={'quantidade': 3}).json()['quantidade'] == 3
    assert client.delete(f'/cart-items/{id_}').json()['ativo'] is False
    assert client.patch(f'/cart-items/{id_}/reactivate', json={'quantidade': 1}).json()['ativo'] is True
    assert client.delete(f'/cart-items/{id_}').status_code == 200
    response = client.post('/cart-items/', json={'cart_id': cart_id, 'product_id': 1, 'quantidade': 2})
    assert response.status_code == 201 and response.json()['ativo'] is True


def test_cart_sync_replaces_items_and_uses_server_prices(commerce_api):
    client = commerce_api
    response = client.put('/carts/me/current', json={'items': [{'product_id': 1, 'quantidade': 2}]})
    assert response.status_code == 200, response.text
    assert Decimal(response.json()['valor_total']) == 200
    assert client.put('/carts/me/current', json={'items': []}).json()['itens'] == []


@pytest.mark.parametrize('product_id,quantity,code', [(999, 1, 404), (1, 21, 400), (1, 0, 422)])
def test_cart_rejects_unavailable_items(commerce_api, product_id, quantity, code):
    id_ = commerce_api.get('/carts/me/current').json()['id']
    response = commerce_api.post(f'/carts/{id_}/items', json={'product_id': product_id, 'quantidade': quantity})
    assert response.status_code == code, response.text
    assert Decimal(commerce_api.get(f'/carts/{id_}/total').json()['total']) == 0


@pytest.mark.parametrize('path', ['/carts/999', '/cart-items/999'])
def test_missing_cart_resources(commerce_api, path):
    assert commerce_api.get(path).status_code == 404
