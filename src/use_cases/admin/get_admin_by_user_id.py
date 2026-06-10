from src.entities.admin import AdminEntity
from src.repositories.admin_repository import AdminRepository


class GetAdminByUserIdUseCase:
    def __init__(self, admin_repository: AdminRepository):
        self.admin_repository = admin_repository

    def execute(self, user_id: int) -> AdminEntity:
        admin = self.admin_repository.get_by_user_id(user_id)
        if not admin:
            raise ValueError("Admin não encontrado")
        return admin
