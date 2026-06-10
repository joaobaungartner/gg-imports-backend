from src.entities.admin import AdminEntity
from src.repositories.admin_repository import AdminRepository


class ManageOrdersUseCase:
    def __init__(self, admin_repository: AdminRepository):
        self.admin_repository = admin_repository
        # TODO: injetar OrderRepository quando disponível

    def validate_admin_permission(self, admin_id: int) -> AdminEntity:
        admin = self.admin_repository.get_by_id(admin_id)
        if not admin:
            raise ValueError("Admin não encontrado")
        if not admin.has_admin_permission():
            raise ValueError("Permissão negada")
        return admin

    def listar_pedidos(self, admin_id: int) -> list:
        admin = self.validate_admin_permission(admin_id)
        admin.gerenciar_pedidos()

        # TODO: integrar com OrderRepository para listar pedidos
        # Exemplo futuro:
        # return self.order_repository.list_all()
        return []

    def atualizar_status_pedido(
        self, admin_id: int, pedido_id: int, status: str
    ) -> None:
        self.validate_admin_permission(admin_id)

        if pedido_id <= 0:
            raise ValueError("Pedido inválido")
        if not status:
            raise ValueError("Status inválido")

        # TODO: integrar com OrderRepository para atualizar status do pedido
        # Exemplo futuro:
        # return self.order_repository.update_status(pedido_id, status)

    def visualizar_detalhes_pedido(self, admin_id: int, pedido_id: int) -> None:
        self.validate_admin_permission(admin_id)

        if pedido_id <= 0:
            raise ValueError("Pedido inválido")

        # TODO: integrar com OrderRepository para buscar detalhes do pedido
        # Exemplo futuro:
        # return self.order_repository.get_by_id(pedido_id)
