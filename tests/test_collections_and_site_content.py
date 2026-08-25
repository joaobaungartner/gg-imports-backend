"""Testes de coleções de produtos e conteúdo do site."""

from fastapi.testclient import TestClient

from src.app import app
from src.utils.product_group_key import build_product_group_key

client = TestClient(app)


def test_admin_collections_require_auth():
    assert client.get("/admin/product-collections/promotions").status_code == 401
    assert client.put(
        "/admin/product-collections/promotions",
        json={"group_keys": []},
    ).status_code == 401
    assert client.get("/admin/product-collections/launches").status_code == 401


def test_admin_how_to_buy_requires_auth():
    assert client.put(
        "/admin/site-content/how-to-buy",
        json={
            "title": "Como comprar",
            "subtitle": "Intro",
            "eyebrow": "Passo a passo",
            "steps": [{"title": "A", "description": "B"}],
        },
    ).status_code == 401


def test_public_how_to_buy_readable():
    response = client.get("/site-content/how-to-buy")
    assert response.status_code == 200
    data = response.json()
    assert data["title"]
    assert len(data["steps"]) >= 1


def test_public_products_collection_invalid():
    response = client.get("/products/?collection=invalid")
    assert response.status_code == 400


def test_public_products_collection_empty_ok():
    response = client.get("/products/?collection=promotions&active=true")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_group_key_is_stable():
    key_a = build_product_group_key(
        nome=" Camisa X ",
        clube="Flamengo",
        category_id=1,
        tipo="Fan",
        imagem_url=None,
        preco="199.90",
    )
    key_b = build_product_group_key(
        nome="camisa x",
        clube="flamengo",
        category_id=1,
        tipo="fan",
        imagem_url=None,
        preco="199.90",
    )
    assert key_a == key_b
