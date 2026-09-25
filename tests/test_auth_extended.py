from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from jose import JWTError
from jose.exceptions import ExpiredSignatureError

from src.database.database import get_db
from src.entities.user import UserEntity, UserRole
from src.entities.address import AddressEntity
from src.middlewares import auth
from src.routes import auth_routes as routes
from src.utils.jwt import create_access_token, decode_access_token
from src.utils.password import hash_password, verify_password
from src.use_cases.auth import login_with_jwt


@pytest.fixture
def user():
    return UserEntity(1, 'Buyer', 'buyer@example.com', hash_password('password123'), data_cadastro=datetime(2025, 1, 1))


@pytest.mark.parametrize('case', ['none', 'invalid', 'expired', 'no_subject', 'bad_subject', 'missing_user', 'inactive', 'valid'])
def test_token_resolution(monkeypatch, user, case):
    repo = Mock()
    repo.get_by_id.return_value = None if case == 'missing_user' else user
    user.ativo = case != 'inactive'
    monkeypatch.setattr(auth, 'UserRepository', lambda db: repo)
    token = create_access_token({'sub': '1'})
    if case == 'none': token = None
    if case == 'invalid': token = 'invalid'
    if case == 'expired': token = create_access_token({'sub': '1'}, timedelta(days=-1))
    if case == 'no_subject': token = create_access_token({})
    if case == 'bad_subject': token = create_access_token({'sub': 'abc'})
    assert auth.get_optional_user(token, Mock()) == (user if case == 'valid' else None)
    if case == 'valid':
        assert auth.get_current_user(token, Mock()) is user
    else:
        with pytest.raises(HTTPException) as error:
            auth.get_current_user(token, Mock())
        assert error.value.status_code == (403 if case == 'inactive' else 401)


@pytest.mark.parametrize('role', list(UserRole))
def test_role_guards(user, role):
    user.role = role
    for guard, required in [(auth.get_current_admin, UserRole.ADMIN), (auth.get_current_client, UserRole.CLIENTE)]:
        if role == required: assert guard(user) is user
        else:
            with pytest.raises(HTTPException) as error: guard(user)
            assert error.value.status_code == 403


@pytest.mark.parametrize('guard', [auth.require_same_user_or_admin, auth.require_admin_or_self, auth.ensure_client_access_by_user_id])
def test_user_ownership(user, guard):
    guard(1, user)
    with pytest.raises(HTTPException) as error: guard(2, user)
    assert error.value.status_code == 403
    user.role = UserRole.ADMIN
    guard(2, user)


@pytest.mark.parametrize('guard,repo_name,field', [
    (auth.ensure_cart_owner_or_admin, 'CartRepository', 'client_id'),
    (auth.ensure_cart_item_owner_or_admin, 'CartItemRepository', 'cart_id'),
    (auth.ensure_order_item_owner_or_admin, 'OrderItemRepository', 'order_id'),
    (auth.ensure_address_owner_or_admin, 'AddressRepository', 'client_id'),
    (auth.ensure_payment_owner_or_admin, 'PaymentRepository', 'order_id'),
    (auth.ensure_payment_access_by_order, 'OrderRepository', 'client_id'),
])
def test_resource_ownership(monkeypatch, user, guard, repo_name, field):
    repos = {}
    for name in ['ClientRepository', 'CartRepository', 'OrderRepository', 'PaymentRepository', 'AddressRepository', 'CartItemRepository', 'OrderItemRepository']:
        repo = Mock()
        repo.get_by_id.return_value = SimpleNamespace(id=1, client_id=1, order_id=1, cart_id=1)
        repos[name] = repo
        monkeypatch.setattr(auth, name, lambda db, repo=repo: repo)
    guard(1, user, Mock())
    repos['ClientRepository'].get_by_id.return_value = SimpleNamespace(id=2)
    with pytest.raises(HTTPException) as error: guard(1, user, Mock())
    assert error.value.status_code == 403
    user.role = UserRole.ADMIN
    guard(1, user, Mock())
    repos[repo_name].get_by_id.return_value = None
    with pytest.raises(HTTPException) as error: guard(1, user, Mock())
    assert error.value.status_code == 404


def test_client_cpf_ownership(monkeypatch, user):
    repo = Mock()
    monkeypatch.setattr(auth, 'ClientRepository', lambda db: repo)
    repo.get_by_cpf.return_value = user
    auth.ensure_client_access_by_cpf('123', user, Mock())
    repo.get_by_cpf.return_value = None
    with pytest.raises(HTTPException) as error: auth.ensure_client_access_by_cpf('123', user, Mock())
    assert error.value.status_code == 403
    user.role = UserRole.ADMIN
    auth.ensure_client_access_by_cpf('123', user, Mock())


def test_guest_order_policy(monkeypatch, user):
    repo = Mock()
    monkeypatch.setattr(auth, 'OrderRepository', lambda db: repo)
    repo.get_by_id.return_value = SimpleNamespace(client_id=None)
    auth.ensure_order_owner_or_admin(1, None, Mock(), allow_public_guest=True)
    for current in [None, user]:
        with pytest.raises(HTTPException) as error: auth.ensure_order_owner_or_admin(1, current, Mock())
        assert error.value.status_code == 403
    user.role = UserRole.ADMIN
    auth.ensure_order_owner_or_admin(1, user, Mock())
    repo.get_by_id.return_value.client_id = 1
    with pytest.raises(HTTPException) as error: auth.ensure_order_owner_or_admin(1, None, Mock())
    assert error.value.status_code == 401


@pytest.fixture
def auth_client(monkeypatch, user):
    repo, notifications = Mock(), Mock()
    repo.get_by_email.return_value = user
    repo.get_by_id.return_value = user
    monkeypatch.setattr(routes, 'UserRepository', lambda db: repo)
    monkeypatch.setattr(routes, 'NotificationService', lambda repository: notifications)
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[get_db] = lambda: Mock()
    app.dependency_overrides[auth.get_current_user] = lambda: user
    with TestClient(app) as client:
        yield client, repo, notifications


@pytest.mark.parametrize('case,code', [('valid', 200), ('missing', 401), ('password', 401), ('inactive', 403)])
def test_login(auth_client, user, case, code):
    client, repo, _ = auth_client
    if case == 'missing': repo.get_by_email.return_value = None
    if case == 'inactive': user.ativo = False
    response = client.post('/auth/login', json={'email': user.email, 'senha': 'wrong' if case == 'password' else 'password123'})
    assert response.status_code == code
    if code == 200:
        claims = decode_access_token(response.json()['access_token'])
        assert claims['sub'] == '1' and claims['purpose'] == 'access'
        assert response.json()['token_type'] == 'bearer'


def test_token_generation_failure(monkeypatch, user):
    authenticate = Mock()
    authenticate.execute.return_value = user
    monkeypatch.setattr(login_with_jwt, 'create_access_token', Mock(side_effect=RuntimeError('failure')))
    with pytest.raises(ValueError, match='Erro ao gerar token'):
        login_with_jwt.LoginWithJwtUseCase(authenticate).execute(user.email, 'password123')


@pytest.mark.parametrize('case', ['valid', 'missing', 'inactive'])
def test_forgot_password_does_not_disclose_account(auth_client, user, case):
    client, repo, notifications = auth_client
    if case == 'missing': repo.get_by_email.return_value = None
    if case == 'inactive': user.ativo = False
    response = client.post('/auth/password/forgot', json={'email': user.email})
    assert response.status_code == 200
    assert 'Se o e-mail' in response.json()['message']
    assert notifications.email.call_count == (1 if case == 'valid' else 0)
    if case == 'valid':
        token = notifications.email.call_args.args[3].split('token=')[1]
        claims = decode_access_token(token, expected_purpose='password_reset')
        assert claims['sub'] == '1'
        assert claims['fp'] == routes._password_fingerprint(user.senha_hash)


@pytest.mark.parametrize('action', ['password/reset', 'email/verify'])
@pytest.mark.parametrize('case', ['valid', 'missing', 'stale', 'expired', 'wrong_purpose'])
def test_action_tokens(auth_client, user, action, case):
    client, repo, _ = auth_client
    purpose = 'password_reset' if action.startswith('password') else 'email_verify'
    claims = {'sub': '1', 'purpose': purpose, 'fp': routes._password_fingerprint(user.senha_hash), 'email': user.email}
    if case == 'missing': repo.get_by_id.return_value = None
    if case == 'stale': claims.update(fp='old', email='old@example.com')
    if case == 'wrong_purpose': claims['purpose'] = 'access'
    token = create_access_token(claims, timedelta(days=-1 if case == 'expired' else 1))
    response = client.post('/auth/' + action, json={'token': token, 'nova_senha': 'new-password'})
    assert response.status_code == (200 if case == 'valid' else 400)
    if case != 'valid': repo.update.assert_not_called()
    elif purpose == 'password_reset': assert verify_password('new-password', repo.update.call_args.args[1]['senha_hash'])
    else: repo.update.assert_called_once_with(1, {'email_verificado': True})


@pytest.mark.parametrize('correct', [True, False])
def test_change_password(auth_client, correct):
    client, repo, _ = auth_client
    response = client.post('/auth/password/change', json={'senha_atual': 'password123' if correct else 'bad', 'nova_senha': 'changed123'})
    assert response.status_code == (200 if correct else 400)
    if correct: assert verify_password('changed123', repo.update.call_args.args[1]['senha_hash'])
    else: repo.update.assert_not_called()


@pytest.mark.parametrize('verified', [True, False])
def test_email_verification_request(auth_client, user, verified):
    client, _, notifications = auth_client
    user.email_verificado = verified
    assert client.post('/auth/email/request-verification').status_code == 200
    assert notifications.email.call_count == (0 if verified else 1)


@pytest.mark.parametrize('case', ['admin', 'no_client', 'no_address', 'address'])
def test_profile(auth_client, user, monkeypatch, case):
    client, _, _ = auth_client
    clients, addresses = Mock(), Mock()
    monkeypatch.setattr(routes, 'ClientRepository', lambda db: clients)
    monkeypatch.setattr(routes, 'AddressRepository', lambda db: addresses)
    clients.get_by_user_id.return_value = None if case == 'no_client' else SimpleNamespace(client_id=2, cpf='123')
    addresses.get_by_client_id.return_value = [AddressEntity(3, 2, 'Rua', '1', 'Centro', 'SP', 'SP', '01001000', ativo=case == 'address')]
    if case == 'admin': user.role = UserRole.ADMIN
    response = client.get('/auth/me')
    assert response.status_code == 200
    assert (response.json()['endereco'] is not None) == (case == 'address')
