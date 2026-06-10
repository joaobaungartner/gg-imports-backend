from src.entities.product import ProductEntity
from src.repositories.product_repository import ProductRepository


class SearchProductsUseCase:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def execute(
        self, query: str, apenas_ativos: bool = True
    ) -> list[ProductEntity]:
        query_normalizado = query.strip()
        if not query_normalizado:
            return []

        return self.product_repository.search(
            query_normalizado, apenas_ativos=apenas_ativos
        )
