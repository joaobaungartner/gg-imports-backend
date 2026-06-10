from src.entities.product import ProductEntity
from src.repositories.category_repository import CategoryRepository
from src.repositories.product_repository import ProductRepository


class ListProductsByCategoryUseCase:
    def __init__(
        self,
        category_repository: CategoryRepository,
        product_repository: ProductRepository,
    ):
        self.category_repository = category_repository
        self.product_repository = product_repository

    def execute(self, category_id: int) -> list[ProductEntity]:
        category = self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError("Categoria não encontrada")

        return self.product_repository.list_by_category(category_id)
