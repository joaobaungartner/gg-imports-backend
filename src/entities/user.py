import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


class UserRole(str, Enum):
    CLIENTE = "CLIENTE"
    ADMIN = "ADMIN"


@dataclass
class UserEntity:
    id: int | None
    nome: str
    email: str
    senha_hash: str
    telefone: str | None = None
    data_cadastro: datetime | None = None
    role: UserRole = UserRole.CLIENTE
    ativo: bool = True

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome não pode ser vazio")
        if not self.verificar_email():
            raise ValueError("Email inválido")
        if not self.senha_hash:
            raise ValueError("Senha hash não pode ser vazia")

    def verificar_email(self) -> bool:
        return bool(EMAIL_REGEX.match(self.email))

    def atualizar_perfil(
        self,
        nome: str | None = None,
        telefone: str | None = None,
    ) -> None:
        if nome is not None:
            if not nome.strip():
                raise ValueError("Nome não pode ser vazio")
            self.nome = nome.strip()
        if telefone is not None:
            self.telefone = telefone

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def is_cliente(self) -> bool:
        return self.role == UserRole.CLIENTE
