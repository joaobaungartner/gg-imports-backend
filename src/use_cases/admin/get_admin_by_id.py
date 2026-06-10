from src.entities.admin import AdminEntity
from src.repositories.admin_repository import AdminRepository


class GetAdminByIdUseCase:
    def __init__(self, admin_repository: AdminRepository):
        self.admin_repository = admin_repository

    def execute(self, admin_id: int) -> AdminEntity:
        admin = self.admin_repository.get_by_id(admin_id)
        if not admin:
            raise ValueError("Admin não encontrado")
        return admin
