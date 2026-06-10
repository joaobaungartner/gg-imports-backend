from src.entities.category import CategoryEntity
from src.repositories.category_repository import CategoryRepository


class UpdateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(
        self,
        category_id: int,
        nome: str | None = None,
        descricao: str | None = None,
        ativo: bool | None = None,
    ) -> CategoryEntity:
        category = self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError("Categoria não encontrada")

        if nome is not None:
            nome_normalizado = nome.strip()
            if not nome_normalizado:
                raise ValueError("Nome da categoria é obrigatório")
            if (
                nome_normalizado != category.nome
                and self.category_repository.name_exists(nome_normalizado)
            ):
                raise ValueError("Categoria já cadastrada")

        category.atualizar_categoria(nome=nome, descricao=descricao, ativo=ativo)

        update_data = {}
        if nome is not None:
            update_data["nome"] = category.nome
        if descricao is not None:
            update_data["descricao"] = category.descricao
        if ativo is not None:
            update_data["ativo"] = category.ativo

        if not update_data:
            return category

        updated_category = self.category_repository.update(category_id, update_data)
        if not updated_category:
            raise ValueError("Categoria não encontrada")

        return updated_category
