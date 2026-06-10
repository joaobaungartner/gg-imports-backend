from src.entities.category import CategoryEntity
from src.repositories.category_repository import CategoryRepository
from src.repositories.product_repository import ProductRepository


class DeleteCategoryUseCase:
    def __init__(
        self,
        category_repository: CategoryRepository,
        product_repository: ProductRepository,
    ):
        self.category_repository = category_repository
        self.product_repository = product_repository
        # TODO: validar permissão de Admin quando middleware existir

    def _has_linked_products(self, category_id: int) -> bool:
        produtos = self.product_repository.list_by_category(category_id)
        return any(produto.ativo for produto in produtos)

    def execute(self, category_id: int) -> CategoryEntity:
        category = self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError("Categoria não encontrada")

        if self._has_linked_products(category_id):
            raise ValueError("Não é possível deletar categoria com produtos vinculados")

        deactivated = self.category_repository.deactivate(category_id)
        if not deactivated:
            raise ValueError("Categoria não encontrada")

        return deactivated
