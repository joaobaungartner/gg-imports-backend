"""Regressões de segurança para criação pública de usuários."""

from fastapi.testclient import TestClient

from src.app import app


client = TestClient(app)

USER_PAYLOAD = {
    "nome": "Usuário teste",
    "email": "usuario@example.com",
    "senha": "senha-segura",
    "telefone": "11999999999",
}


def test_generic_user_creation_endpoint_is_not_public():
    response = client.post(
        "/users/",
        json={**USER_PAYLOAD, "role": "ADMIN"},
    )

    assert response.status_code == 404


def test_public_client_signup_rejects_role_injection():
    response = client.post(
        "/clients/",
        json={**USER_PAYLOAD, "cpf": "12345678901", "role": "ADMIN"},
    )

    assert response.status_code == 422


def test_admin_creation_still_requires_admin_authentication():
    response = client.post("/admins/", json=USER_PAYLOAD)

    assert response.status_code == 401
