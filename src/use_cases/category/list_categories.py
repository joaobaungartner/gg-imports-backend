from src.entities.category import CategoryEntity
from src.repositories.category_repository import CategoryRepository


class ListCategoriesUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(self, ativo: bool | None = None) -> list[CategoryEntity]:
        if ativo is True:
            return self.category_repository.list_active()
        if ativo is False:
            return [
                category
                for category in self.category_repository.list_all()
                if not category.ativo
            ]
        return self.category_repository.list_all()
