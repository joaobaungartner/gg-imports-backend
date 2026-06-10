from src.entities.admin import AdminEntity
from src.entities.user import UserEntity, UserRole
from src.repositories.admin_repository import AdminRepository
from src.repositories.user_repository import UserRepository
from src.utils.password import hash_password


class CreateAdminUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        admin_repository: AdminRepository,
    ):
        self.user_repository = user_repository
        self.admin_repository = admin_repository

    def execute(
        self,
        nome: str,
        email: str,
        senha: str,
        telefone: str | None = None,
    ) -> AdminEntity:
        if self.user_repository.email_exists(email):
            raise ValueError("Email já cadastrado")

        senha_hash = hash_password(senha)

        user = UserEntity(
            id=None,
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            telefone=telefone,
            role=UserRole.ADMIN,
        )
        created_user = self.user_repository.create(user)

        admin = AdminEntity(
            id=created_user.id,
            nome=created_user.nome,
            email=created_user.email,
            senha_hash=created_user.senha_hash,
            telefone=created_user.telefone,
            data_cadastro=created_user.data_cadastro,
            role=UserRole.ADMIN,
        )

        return self.admin_repository.create(admin)
