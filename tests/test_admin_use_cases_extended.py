from unittest.mock import Mock

import pytest

from src.entities.admin import AdminEntity
from src.entities.user import UserEntity
from src.repositories.admin_repository import AdminRepository
from src.repositories.user_repository import UserRepository
from src.repositories.client_repository import ClientRepository
from src.use_cases.admin.update_admin import UpdateAdminUseCase
from src.use_cases.admin.deactivate_admin import DeactivateAdminUseCase
from src.use_cases.client.deactivate_client import DeactivateClientUseCase
from src.use_cases.admin.manage_users import ManageUsersUseCase
from src.use_cases.admin.manage_products import ManageProductsUseCase
from src.use_cases.admin.manage_orders import ManageOrdersUseCase


def test_admin_update_and_deactivation_with_complete_dependencies(db_session):
    users, admins = UserRepository(db_session), AdminRepository(db_session)
    user = users.create(UserEntity(None, 'Admin', 'admin@example.com', 'test'))
    admin = admins.create(AdminEntity(user.id, user.nome, user.email, user.senha_hash))
    updated = UpdateAdminUseCase(users, admins).execute(admin.admin_id, nome='Changed', telefone='123', email='changed@example.com')
    assert (updated.nome, updated.telefone, updated.email) == ('Changed', '123', 'changed@example.com')
    assert not DeactivateAdminUseCase(users, admins).execute(admin.admin_id).ativo
    assert not users.get_by_id(user.id).ativo


def test_client_deactivation_with_complete_dependencies(commerce_api, db_session):
    users, clients = UserRepository(db_session), ClientRepository(db_session)
    assert not DeactivateClientUseCase(users, clients).execute(1).ativo
    assert not users.get_by_id(1).ativo


@pytest.mark.parametrize('cls', [DeactivateAdminUseCase, DeactivateClientUseCase])
@pytest.mark.parametrize('case', ['missing', 'entity_update_missing', 'user_update_missing'])
def test_deactivation_missing_records(cls, case):
    users, profiles = Mock(), Mock()
    if case == 'missing': profiles.get_by_id.return_value = None
    if case == 'entity_update_missing': profiles.deactivate.return_value = None
    if case == 'user_update_missing': users.deactivate.return_value = None
    with pytest.raises(ValueError): cls(users, profiles).execute(1)


def test_manage_users_checks_permissions_and_updates_persistence(db_session):
    users, admins = UserRepository(db_session), Mock()
    user = users.create(UserEntity(None, 'Buyer', 'buyer@example.com', 'test'))
    admin = AdminEntity(2, 'Admin', 'admin@example.com', 'test')
    admins.get_by_id.return_value = admin
    use_case = ManageUsersUseCase(admins, users)
    assert use_case.listar_usuarios(2)[0].id == user.id
    assert use_case.buscar_usuario(2, user.id).email == user.email
    assert not use_case.desativar_usuario(2, user.id).ativo
    assert use_case.ativar_usuario(2, user.id).ativo
    for operation in (use_case.buscar_usuario, use_case.desativar_usuario, use_case.ativar_usuario):
        with pytest.raises(ValueError): operation(2, 999)
    admin.ativo = False
    with pytest.raises(ValueError, match='Permissão'): use_case.listar_usuarios(2)
    admins.get_by_id.return_value = None
    with pytest.raises(ValueError, match='Admin'): use_case.listar_usuarios(2)


@pytest.mark.parametrize('cls', [ManageProductsUseCase, ManageOrdersUseCase])
def test_admin_management_permission_guards(cls):
    repo = Mock()
    admin = AdminEntity(1, 'Admin', 'admin@example.com', 'test')
    repo.get_by_id.return_value = admin
    use_case = cls(repo)
    assert use_case.validate_admin_permission(1) is admin
    admin.ativo = False
    with pytest.raises(ValueError, match='Permissão'): use_case.validate_admin_permission(1)
    repo.get_by_id.return_value = None
    with pytest.raises(ValueError, match='Admin'): use_case.validate_admin_permission(1)
