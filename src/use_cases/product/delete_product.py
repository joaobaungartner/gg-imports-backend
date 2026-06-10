from src.entities.product import ProductEntity
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.product_repository import ProductRepository


class DeleteProductUseCase:
    def __init__(
        self,
        product_repository: ProductRepository,
        order_item_repository: OrderItemRepository,
    ):
        self.product_repository = product_repository
        self.order_item_repository = order_item_repository
        # TODO: validar permissão de Admin quando middleware existir

    def _has_linked_orders(self, product_id: int) -> bool:
        itens = self.order_item_repository.get_by_product_id(product_id)
        return any(item.ativo for item in itens)

    def execute(self, product_id: int) -> ProductEntity:
        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")

        if self._has_linked_orders(product_id):
            raise ValueError("Não é possível deletar produto com pedidos vinculados")

        deactivated = self.product_repository.deactivate(product_id)
        if not deactivated:
            raise ValueError("Produto não encontrado")

        return deactivated
