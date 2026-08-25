from src.entities.order import OrderEntity
from src.repositories.order_repository import OrderRepository


class UpdateAdminOrderNotesUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def execute(self, order_id: int, admin_notes: str | None) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        updated = self.order_repository.update_admin_notes(order_id, admin_notes)
        if not updated:
            raise ValueError("Pedido não encontrado")
        return updated
