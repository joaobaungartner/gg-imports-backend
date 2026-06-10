from src.entities.category import CategoryEntity
from src.repositories.category_repository import CategoryRepository


class CreateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(self, nome: str, descricao: str | None = None) -> CategoryEntity:
        nome_normalizado = nome.strip()
        if not nome_normalizado:
            raise ValueError("Nome da categoria é obrigatório")

        if self.category_repository.name_exists(nome_normalizado):
            raise ValueError("Categoria já cadastrada")

        category = CategoryEntity(
            id=None,
            nome=nome_normalizado,
            descricao=descricao,
            ativo=True,
        )

        return self.category_repository.create(category)
