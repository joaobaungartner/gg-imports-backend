from src.entities.category import CategoryEntity
from src.repositories.category_repository import CategoryRepository


class DeleteCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository
        # TODO: validar permissão de Admin quando middleware existir
        # TODO: ProductRepository - validar produtos vinculados antes de deletar

    def _has_linked_products(self, category_id: int) -> bool:
        # TODO: ProductRepository.get_by_category_id(category_id) quando existir
        return False

    def execute(self, category_id: int) -> CategoryEntity:
        category = self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError("Categoria não encontrada")

        if self._has_linked_products(category_id):
            raise ValueError("Não é possível deletar categoria com produtos vinculados")

        # Preferir desativação lógica em vez de delete físico
        deactivated = self.category_repository.deactivate(category_id)
        if not deactivated:
            raise ValueError("Categoria não encontrada")

        return deactivated
