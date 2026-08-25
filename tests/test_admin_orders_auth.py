"""Testes de autorização nos endpoints administrativos de pedidos."""

from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_admin_orders_requires_auth():
    response = client.get("/admin/orders/")
    assert response.status_code == 401


def test_admin_orders_summary_requires_auth():
    response = client.get("/admin/orders/summary")
    assert response.status_code == 401


def test_admin_order_detail_requires_auth():
    response = client.get("/admin/orders/1")
    assert response.status_code == 401


def test_admin_update_status_requires_auth():
    response = client.patch("/admin/orders/1/status", json={"status": "PAID"})
    assert response.status_code == 401


def test_admin_update_notes_requires_auth():
    response = client.patch(
        "/admin/orders/1/notes", json={"admin_notes": "teste"}
    )
    assert response.status_code == 401


def test_admin_history_requires_auth():
    response = client.get("/admin/orders/1/history")
    assert response.status_code == 401


def test_client_orders_me_requires_auth():
    response = client.get("/orders/me")
    assert response.status_code == 401
