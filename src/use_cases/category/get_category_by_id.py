from src.entities.category import CategoryEntity
from src.repositories.category_repository import CategoryRepository


class GetCategoryByIdUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    def execute(self, category_id: int) -> CategoryEntity:
        category = self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError("Categoria não encontrada")
        return category
