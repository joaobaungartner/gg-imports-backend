from src.entities.user import UserEntity, UserRole
from src.repositories.user_repository import UserRepository
from src.utils.password import hash_password


class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(
        self,
        nome: str,
        email: str,
        senha: str,
        telefone: str | None = None,
        role: UserRole | None = None,
    ) -> UserEntity:
        if self.user_repository.email_exists(email):
            raise ValueError("Email já cadastrado")

        user_role = role or UserRole.CLIENTE
        senha_hash = hash_password(senha)

        user = UserEntity(
            id=None,
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            telefone=telefone,
            role=user_role,
        )

        return self.user_repository.create(user)
