from src.entities.admin import AdminEntity
from src.repositories.admin_repository import AdminRepository
from src.repositories.user_repository import UserRepository


class UpdateAdminUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        admin_repository: AdminRepository,
    ):
        self.user_repository = user_repository
        self.admin_repository = admin_repository

    def execute(
        self,
        admin_id: int,
        nome: str | None = None,
        telefone: str | None = None,
        email: str | None = None,
    ) -> AdminEntity:
        admin = self.admin_repository.get_by_id(admin_id)
        if not admin:
            raise ValueError("Admin não encontrado")

        admin.atualizar_perfil(nome=nome, telefone=telefone)

        user_update_data = {}
        if nome is not None:
            user_update_data["nome"] = admin.nome
        if telefone is not None:
            user_update_data["telefone"] = admin.telefone

        if email is not None:
            if email != admin.email and self.user_repository.email_exists(email):
                raise ValueError("Email já cadastrado")
            admin.email = email
            if not admin.verificar_email():
                raise ValueError("Email inválido")
            user_update_data["email"] = admin.email

        if user_update_data:
            updated_user = self.user_repository.update(admin.id, user_update_data)
            if not updated_user:
                raise ValueError("Usuário não encontrado")

        return self.admin_repository.get_by_id(admin_id)
