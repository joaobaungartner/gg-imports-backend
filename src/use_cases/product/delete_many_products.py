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
        self.product_repository = product_repository
        self.delete_product_use_case = DeleteProductUseCase(
            product_repository, order_item_repository
        )

    def execute(self, product_ids: list[int]) -> list[ProductEntity]:
        deleted: list[ProductEntity] = []

        try:
            for product_id in dict.fromkeys(product_ids):
                deleted.append(self.delete_product_use_case.execute(product_id, commit=False))
            self.product_repository.db.commit()
        except Exception:
            self.product_repository.db.rollback()
            raise

        return deleted
