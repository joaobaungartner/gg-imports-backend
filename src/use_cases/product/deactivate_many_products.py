from src.entities.product import ProductEntity
from src.repositories.product_repository import ProductRepository


class DeactivateManyProductsUseCase:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def execute(self, product_ids: list[int]) -> list[ProductEntity]:
        deactivated: list[ProductEntity] = []

        for product_id in product_ids:
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise ValueError(f"Produto não encontrado: {product_id}")

            result = self.product_repository.deactivate(product_id)
            if not result:
                raise ValueError(f"Produto não encontrado: {product_id}")

            deactivated.append(result)

        return deactivated
