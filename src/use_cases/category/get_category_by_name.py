from src.entities.category import CategoryEntity
from src.repositories.category_repository import CategoryRepository


class GetCategoryByNameUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    def execute(self, nome: str) -> CategoryEntity:
        nome_normalizado = nome.strip()
        if not nome_normalizado:
            raise ValueError("Nome da categoria é obrigatório")

        category = self.category_repository.get_by_name(nome_normalizado)
        if not category:
            raise ValueError("Categoria não encontrada")
        return category
