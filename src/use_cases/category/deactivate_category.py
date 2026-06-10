from src.entities.category import CategoryEntity
from src.repositories.category_repository import CategoryRepository


class DeactivateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(self, category_id: int) -> CategoryEntity:
        category = self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError("Categoria não encontrada")

        deactivated = self.category_repository.deactivate(category_id)
        if not deactivated:
            raise ValueError("Categoria não encontrada")

        return deactivated
