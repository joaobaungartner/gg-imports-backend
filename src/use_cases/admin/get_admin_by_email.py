from src.entities.admin import AdminEntity
from src.repositories.admin_repository import AdminRepository


class GetAdminByEmailUseCase:
    def __init__(self, admin_repository: AdminRepository):
        self.admin_repository = admin_repository

    def execute(self, email: str) -> AdminEntity:
        admin = self.admin_repository.get_by_email(email)
        if not admin:
            raise ValueError("Admin não encontrado")
        return admin
