from src.entities.order import OrderEntity
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.use_cases.order_item.create_order_item import CreateOrderItemUseCase


class AddOrderItemUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        order_item_repository: OrderItemRepository,
        product_repository: ProductRepository,
    ):
        self.order_repository = order_repository
        self._create_order_item = CreateOrderItemUseCase(
            order_repository, order_item_repository, product_repository
        )

    def execute(
        self,
        order_id: int,
        product_id: int,
        quantidade: int,
    ) -> OrderEntity:
        self._create_order_item.execute(order_id, product_id, quantidade)

        updated_order = self.order_repository.get_by_id(order_id)
        if not updated_order:
            raise ValueError("Pedido não encontrado")

        return updated_order
