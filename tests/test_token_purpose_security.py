"""Signed email-action tokens must never grant an authenticated session."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from src.config.config import get_settings
from src.database.database import get_db
from src.middlewares.auth import get_current_admin, get_current_user, get_optional_user
from src.routes.auth_routes import _decode_action_token
from src.use_cases.auth.login_with_jwt import LoginWithJwtUseCase
from src.utils.jwt import create_access_token, decode_access_token


@pytest.fixture
def protected_client(monkeypatch):
    repository = Mock()
    repository.get_by_id.return_value = SimpleNamespace(
        id=123, ativo=True, role="ADMIN"
    )
    monkeypatch.setattr("src.middlewares.auth.UserRepository", lambda db: repository)
    app = FastAPI()
    app.dependency_overrides[get_db] = lambda: None

    @app.get("/required")
    def required(user=Depends(get_current_user)):
        return {"id": user.id}

    @app.get("/admin")
    def admin(user=Depends(get_current_admin)):
        return {"id": user.id}

    @app.get("/optional")
    def optional(user=Depends(get_optional_user)):
        return {"authenticated": user is not None}

    with TestClient(app) as client:
        yield client, repository


@pytest.mark.parametrize("purpose", ["password_reset", "email_verify", "unknown", None])
def test_non_access_tokens_cannot_authenticate(protected_client, purpose):
    client, repository = protected_client
    settings = get_settings()
    claims = {"sub": "123", "exp": 4102444800}
    if purpose is not None:
        claims["purpose"] = purpose
    token = jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/required", headers=headers).status_code == 401
    assert client.get("/admin", headers=headers).status_code == 401
    assert client.get("/optional", headers=headers).json() == {"authenticated": False}
    repository.get_by_id.assert_not_called()


def test_login_issues_usable_access_token(protected_client):
    client, repository = protected_client
    user = repository.get_by_id.return_value
    user.email = "admin@example.com"
    authenticator = Mock()
    authenticator.execute.return_value = user
    result = LoginWithJwtUseCase(authenticator).execute(user.email, "password")
    assert decode_access_token(result.access_token)["purpose"] == "access"
    headers = {"Authorization": f"Bearer {result.access_token}"}
    assert client.get("/required", headers=headers).status_code == 200
    assert client.get("/admin", headers=headers).status_code == 200
    assert client.get("/optional", headers=headers).json() == {"authenticated": True}


@pytest.mark.parametrize("purpose", ["password_reset", "email_verify"])
def test_action_token_remains_valid_only_for_its_action(purpose):
    from fastapi import HTTPException

    token = create_access_token({"sub": "123", "purpose": purpose})
    assert _decode_action_token(token, purpose)["sub"] == "123"
    other = "email_verify" if purpose == "password_reset" else "password_reset"
    for invalid_token in (token, create_access_token({"sub": "123"})):
        with pytest.raises(HTTPException) as error:
            _decode_action_token(invalid_token, other)
        assert error.value.status_code == 400


def test_expired_access_token_is_rejected(protected_client):
    client, repository = protected_client
    token = create_access_token({"sub": "123"}, timedelta(seconds=-60))
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/required", headers=headers).status_code == 401
    assert client.get("/optional", headers=headers).json() == {"authenticated": False}
    repository.get_by_id.assert_not_called()
