from src.entities.product import ProductEntity
from src.repositories.product_repository import ProductRepository


class ActivateManyProductsUseCase:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def execute(self, product_ids: list[int]) -> list[ProductEntity]:
        activated: list[ProductEntity] = []

        for product_id in product_ids:
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise ValueError(f"Produto não encontrado: {product_id}")

            result = self.product_repository.activate(product_id)
            if not result:
                raise ValueError(f"Produto não encontrado: {product_id}")

            activated.append(result)

        return activated
