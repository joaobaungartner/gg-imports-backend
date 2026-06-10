from src.entities.order import OrderEntity
from src.repositories.order_repository import OrderRepository


class ListOrdersUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
        # TODO: injetar AdminRepository para validar permissão de Admin

    def execute(
        self,
        status: str | None = None,
        client_id: int | None = None,
        admin_id: int | None = None,
    ) -> list[OrderEntity]:
        # TODO: validar permissão de Admin quando admin_id for informado
        # Exemplo futuro:
        # if admin_id is not None:
        #     admin = self.admin_repository.get_by_id(admin_id)
        #     if not admin or not admin.has_admin_permission():
        #         raise ValueError("Permissão negada")

        if status and client_id:
            orders = self.order_repository.get_by_client_id(client_id)
            return [order for order in orders if order.status.value == status]

        if status:
            return self.order_repository.list_by_status(status)

        if client_id:
            return self.order_repository.get_by_client_id(client_id)

        return self.order_repository.list_all()
