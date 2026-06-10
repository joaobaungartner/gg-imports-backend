import re

from src.entities.client import ClientEntity
from src.entities.user import UserEntity, UserRole
from src.repositories.client_repository import ClientRepository
from src.repositories.user_repository import UserRepository
from src.utils.password import hash_password


class CreateClientUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        client_repository: ClientRepository,
    ):
        self.user_repository = user_repository
        self.client_repository = client_repository

    def execute(
        self,
        nome: str,
        email: str,
        senha: str,
        cpf: str,
        telefone: str | None = None,
    ) -> ClientEntity:
        if self.user_repository.email_exists(email):
            raise ValueError("Email já cadastrado")

        cpf_digits = re.sub(r"\D", "", cpf)
        if self.client_repository.cpf_exists(cpf_digits):
            raise ValueError("CPF já cadastrado")

        senha_hash = hash_password(senha)

        user = UserEntity(
            id=None,
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            telefone=telefone,
            role=UserRole.CLIENTE,
        )
        created_user = self.user_repository.create(user)

        client = ClientEntity(
            id=created_user.id,
            nome=created_user.nome,
            email=created_user.email,
            senha_hash=created_user.senha_hash,
            telefone=created_user.telefone,
            data_cadastro=created_user.data_cadastro,
            role=UserRole.CLIENTE,
            cpf=cpf_digits,
        )

        return self.client_repository.create(client)
