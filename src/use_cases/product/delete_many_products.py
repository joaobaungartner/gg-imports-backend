from src.entities.product import ProductEntity
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.product_repository import ProductRepository
from src.use_cases.product.delete_product import DeleteProductUseCase


class DeleteManyProductsUseCase:
    def __init__(
        self,
        product_repository: ProductRepository,
        order_item_repository: OrderItemRepository,
    ):
        self.delete_product_use_case = DeleteProductUseCase(
            product_repository, order_item_repository
        )

    def execute(self, product_ids: list[int]) -> list[ProductEntity]:
        deleted: list[ProductEntity] = []

        for product_id in product_ids:
            deleted.append(self.delete_product_use_case.execute(product_id))

        return deleted
