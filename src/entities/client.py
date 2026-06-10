import re
from dataclasses import dataclass

from src.entities.user import UserEntity, UserRole

CPF_REGEX = re.compile(r"^\d{11}$")


@dataclass
class ClientEntity(UserEntity):
    cpf: str = ""
    client_id: int | None = None

    def __post_init__(self) -> None:
        self.role = UserRole.CLIENTE
        self._validate_cpf()
        super().__post_init__()

    def _validate_cpf(self) -> None:
        if not self.cpf:
            raise ValueError("CPF obrigatório")
        cpf_digits = re.sub(r"\D", "", self.cpf)
        if not CPF_REGEX.match(cpf_digits):
            raise ValueError("CPF inválido")
        self.cpf = cpf_digits

    def atualizar_perfil(
        self,
        nome: str | None = None,
        telefone: str | None = None,
        cpf: str | None = None,
    ) -> None:
        super().atualizar_perfil(nome=nome, telefone=telefone)
        if cpf is not None:
            self.cpf = cpf
            self._validate_cpf()

    def visualizar_pedidos(self) -> list:
        if not self.ativo:
            raise ValueError("Cliente inativo")
        return []

    def adicionar_ao_carrinho(self, produto_id: int, quantidade: int) -> None:
        if not self.ativo:
            raise ValueError("Cliente inativo")
        if produto_id <= 0:
            raise ValueError("Produto inválido")
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
