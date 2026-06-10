from src.entities.category import CategoryEntity
from src.repositories.category_repository import CategoryRepository


class ActivateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(self, category_id: int) -> CategoryEntity:
        category = self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError("Categoria não encontrada")

        activated = self.category_repository.activate(category_id)
        if not activated:
            raise ValueError("Categoria não encontrada")

        return activated
