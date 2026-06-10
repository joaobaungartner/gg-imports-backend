from dataclasses import dataclass

from src.entities.user import UserEntity, UserRole


@dataclass
class AdminEntity(UserEntity):
    admin_id: int | None = None

    def __post_init__(self) -> None:
        self.role = UserRole.ADMIN
        super().__post_init__()

    def has_admin_permission(self) -> bool:
        return self.is_admin() and self.ativo

    def cadastrar_produto(self) -> None:
        if not self.has_admin_permission():
            raise ValueError("Permissão negada")

    def editar_produto(self, produto_id: int) -> None:
        if not self.has_admin_permission():
            raise ValueError("Permissão negada")
        if produto_id <= 0:
            raise ValueError("Produto inválido")

    def remover_produto(self, produto_id: int) -> None:
        if not self.has_admin_permission():
            raise ValueError("Permissão negada")
        if produto_id <= 0:
            raise ValueError("Produto inválido")

    def gerenciar_pedidos(self) -> list:
        if not self.has_admin_permission():
            raise ValueError("Permissão negada")
        return []

    def gerenciar_usuarios(self) -> list:
        if not self.has_admin_permission():
            raise ValueError("Permissão negada")
        return []
