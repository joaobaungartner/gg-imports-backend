from src.entities.admin import AdminEntity
from src.repositories.admin_repository import AdminRepository
from src.repositories.user_repository import UserRepository


class DeactivateAdminUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        admin_repository: AdminRepository,
    ):
        self.user_repository = user_repository
        self.admin_repository = admin_repository

    def execute(self, admin_id: int) -> AdminEntity:
        admin = self.admin_repository.get_by_id(admin_id)
        if not admin:
            raise ValueError("Admin não encontrado")

        deactivated_admin = self.admin_repository.deactivate(admin_id)
        if not deactivated_admin:
            raise ValueError("Admin não encontrado")

        deactivated_user = self.user_repository.deactivate(admin.id)
        if not deactivated_user:
            raise ValueError("Usuário não encontrado")

        return self.admin_repository.get_by_id(admin_id)
