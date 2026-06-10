from src.entities.admin import AdminEntity
from src.entities.user import UserEntity
from src.repositories.admin_repository import AdminRepository
from src.repositories.user_repository import UserRepository
from src.schemas.user_schema import UserResponse


class ManageUsersUseCase:
    def __init__(
        self,
        admin_repository: AdminRepository,
        user_repository: UserRepository,
    ):
        self.admin_repository = admin_repository
        self.user_repository = user_repository

    def validate_admin_permission(self, admin_id: int) -> AdminEntity:
        admin = self.admin_repository.get_by_id(admin_id)
        if not admin:
            raise ValueError("Admin não encontrado")
        if not admin.has_admin_permission():
            raise ValueError("Permissão negada")
        return admin

    def _to_response(self, user: UserEntity) -> UserResponse:
        return UserResponse(
            id=user.id,
            nome=user.nome,
            email=user.email,
            telefone=user.telefone,
            data_cadastro=user.data_cadastro,
            role=user.role.value,
            ativo=user.ativo,
        )

    def listar_usuarios(self, admin_id: int) -> list[UserResponse]:
        self.validate_admin_permission(admin_id)
        users = self.user_repository.list_all()
        return [self._to_response(user) for user in users]

    def buscar_usuario(self, admin_id: int, user_id: int) -> UserResponse:
        self.validate_admin_permission(admin_id)
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        return self._to_response(user)

    def ativar_usuario(self, admin_id: int, user_id: int) -> UserResponse:
        self.validate_admin_permission(admin_id)
        user = self.user_repository.update(user_id, {"ativo": True})
        if not user:
            raise ValueError("Usuário não encontrado")
        return self._to_response(user)

    def desativar_usuario(self, admin_id: int, user_id: int) -> UserResponse:
        self.validate_admin_permission(admin_id)
        user = self.user_repository.deactivate(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        return self._to_response(user)
