from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.parametrize('path', ['/products/', '/products/?active=true&category_id=1&clube=Club&tipo=Fan&tamanho=M',
    '/products/search?q=Shirt', '/products/search?q=Shirt&apenas_ativos=false', '/products/category/1', '/products/name/Shirt',
    '/products/1', '/categories/', '/categories/?active=true', '/categories/1', '/categories/name/Shirts',
    '/coupons/', '/coupons/?active=true', '/coupons/1', '/coupons/code/SAVE10'])
def test_catalog_reads(commerce_api, path):
    response = commerce_api.get(path)
    assert response.status_code == 200, response.text
    assert response.json()


def test_category_lifecycle(commerce_api):
    client = commerce_api
    data = {'nome': 'New category', 'descricao': 'Description'}
    created = client.post('/categories/', json=data)
    assert created.status_code == 201, created.text
    id_ = created.json()['id']
    assert client.post('/categories/', json=data).status_code == 400
    updated = client.put(f'/categories/{id_}', json={'nome': 'Updated', 'descricao': 'New description'})
    assert updated.status_code == 200 and updated.json()['nome'] == 'Updated'
    assert client.patch(f'/categories/{id_}/deactivate').json()['ativo'] is False
    assert client.patch(f'/categories/{id_}/activate').json()['ativo'] is True
    assert client.delete(f'/categories/{id_}').status_code == 200
    assert client.get(f'/categories/{id_}').json()['ativo'] is False


@pytest.mark.parametrize('resource', ['categories', 'products', 'coupons'])
def test_missing_catalog_resources(commerce_api, resource):
    expected = 400 if resource == 'categories' else 404
    assert commerce_api.get(f'/{resource}/999').status_code == expected
    assert commerce_api.patch(f'/{resource}/999/activate').status_code == expected
    assert commerce_api.patch(f'/{resource}/999/deactivate').status_code == expected


def test_coupon_lifecycle(commerce_api):
    client = commerce_api
    payload = {'codigo': ' new20 ', 'desconto': 20, 'validade': '2099-01-01'}
    response = client.post('/coupons/', json=payload)
    assert response.status_code == 201, response.text
    id_ = response.json()['id']
    assert response.json()['codigo'] == 'NEW20'
    assert client.post('/coupons/', json=payload).status_code == 400
    assert client.put(f'/coupons/{id_}', json={'codigo': 'new25', 'desconto': 25, 'validade': '2099-02-01', 'ativo': True}).status_code == 200
    assert client.post('/coupons/validate', json={'codigo': 'NEW25'}).status_code == 200
    # Current route injects a repository where the use case expects a validator.
    # Characterize this existing defect without changing production behavior.
    with pytest.raises(AttributeError, match='execute'):
        client.post('/coupons/apply', json={'codigo': 'NEW25', 'valor_total': 200})
    assert client.patch(f'/coupons/{id_}/deactivate').json()['ativo'] is False
    assert client.post('/coupons/validate', json={'codigo': 'NEW25'}).status_code == 400
    assert client.patch(f'/coupons/{id_}/activate').json()['ativo'] is True
    assert client.post('/coupons/validate', json={'codigo': 'MISSING'}).status_code == 404


def test_product_lifecycle(commerce_api):
    client = commerce_api
    response = client.post('/products/', data={'category_id': 1, 'nome': 'New shirt', 'preco': 50,
        'tamanho': 'G', 'clube': 'Club', 'tipo': 'Fan', 'estoque': 4, 'imagem_url': 'https://example.invalid/image.png'})
    assert response.status_code == 201, response.text
    id_ = response.json()['id']
    changes = dict(category_id=1, nome='Updated shirt', preco=60, tamanho='P', clube='Other', tipo='Player',
        estoque=8, descricao='New description', imagem_url='https://example.invalid/new.png', temporada='2025',
        versao='Home', genero='Unisex', fornecedor='Local', sku='SKU1', ativo=True)
    updated = client.put(f'/products/{id_}', json=changes)
    assert updated.status_code == 200, updated.text
    assert updated.json()['nome'] == changes['nome']
    assert client.patch(f'/products/{id_}/stock', json={'estoque': 5}).json()['estoque'] == 5
    assert client.patch(f'/products/{id_}/stock/increase', json={'quantidade': 2}).json()['estoque'] == 7
    assert client.patch(f'/products/{id_}/stock/decrease', json={'quantidade': 3}).json()['estoque'] == 4
    assert client.post(f'/products/{id_}/availability', json={'quantidade': 5}).json()['disponivel'] is False
    assert client.patch(f'/products/{id_}/stock/decrease', json={'quantidade': 5}).status_code == 400
    assert client.patch(f'/products/{id_}/deactivate').json()['ativo'] is False
    assert client.patch(f'/products/{id_}/activate').json()['ativo'] is True
    assert client.delete(f'/products/{id_}').status_code == 200
    assert client.get(f'/products/{id_}').json()['ativo'] is False


def test_bulk_product_actions(commerce_api):
    client = commerce_api
    for action in ['deactivate', 'activate']:
        response = client.patch(f'/products/{action}-many', json={'product_ids': [1, 1]})
        assert response.status_code == 200, response.text
        assert response.json()['product_ids'] == [1, 1]
        assert client.patch(f'/products/{action}-many', json={'product_ids': [999]}).status_code == 404
    response = client.request('DELETE', '/products/delete-many', json={'product_ids': [1]})
    assert response.status_code == 200, response.text
    assert client.get('/products/1').json()['ativo'] is False


@pytest.mark.parametrize('error', [False, True])
def test_product_upload_uses_storage_boundary(commerce_api, monkeypatch, error):
    storage = Mock()
    storage.upload_product_image = AsyncMock(return_value='https://example.invalid/image.png',
                                            side_effect=ValueError('Invalid image') if error else None)
    monkeypatch.setattr('src.routes.product_routes.StorageService', lambda: storage)
    response = commerce_api.post('/products/', data=dict(category_id=1, nome='Upload', preco=10, tamanho='M',
        clube='Club', tipo='Fan', estoque=1), files={'imagem': ('image.png', b'fake image', 'image/png')})
    assert response.status_code == (400 if error else 201)
    storage.upload_product_image.assert_awaited_once()


def test_collections_and_site_content(commerce_api):
    client = commerce_api
    response = client.get('/admin/product-collections/promotions')
    assert response.status_code == 200, response.text
    key = response.json()['items'][0]['group_key']
    response = client.put('/admin/product-collections/promotions', json={'group_keys': [key, key]})
    assert response.status_code == 200 and response.json()['selected_count'] == 1
    response = client.get('/products/?collection=promotions&active=true&category_id=1&clube=Club&tipo=Fan&tamanho=M')
    assert response.status_code == 200 and len(response.json()) == 1
    assert client.put('/admin/product-collections/promotions', json={'group_keys': ['missing']}).status_code == 404
    assert client.get('/admin/product-collections/invalid').status_code == 400
    assert client.put('/admin/product-collections/promotions', json={'group_keys': []}).status_code == 200
    assert client.get('/products/?collection=promotions').json() == []
    data = client.get('/site-content/how-to-buy').json()
    data['title'] = 'Updated instructions'
    assert client.put('/admin/site-content/how-to-buy', json=data).status_code == 200
    assert client.get('/site-content/how-to-buy').json()['title'] == 'Updated instructions'
    data['title'] = 'Second update'
    assert client.put('/admin/site-content/how-to-buy', json=data).json()['title'] == 'Second update'
