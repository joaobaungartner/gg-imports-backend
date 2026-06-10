from decimal import Decimal

from src.entities.product import ProductEntity
from src.repositories.category_repository import CategoryRepository
from src.repositories.product_repository import ProductRepository


class UpdateProductUseCase:
    def __init__(
        self,
        category_repository: CategoryRepository,
        product_repository: ProductRepository,
    ):
        self.category_repository = category_repository
        self.product_repository = product_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(
        self,
        product_id: int,
        category_id: int | None = None,
        nome: str | None = None,
        descricao: str | None = None,
        preco: float | None = None,
        tamanho: str | None = None,
        clube: str | None = None,
        tipo: str | None = None,
        estoque: int | None = None,
        imagem_url: str | None = None,
        ativo: bool | None = None,
    ) -> ProductEntity:
        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")

        if category_id is not None:
            category = self.category_repository.get_by_id(category_id)
            if not category:
                raise ValueError("Categoria não encontrada")
            if not category.esta_ativa():
                raise ValueError("Categoria inativa")

        preco_decimal = Decimal(str(preco)) if preco is not None else None
        product.atualizar_produto(
            category_id=category_id,
            nome=nome,
            descricao=descricao,
            preco=preco_decimal,
            tamanho=tamanho,
            clube=clube,
            tipo=tipo,
            estoque=estoque,
            imagem_url=imagem_url,
            ativo=ativo,
        )

        update_data = {}
        if category_id is not None:
            update_data["category_id"] = product.category_id
        if nome is not None:
            update_data["nome"] = product.nome
        if descricao is not None:
            update_data["descricao"] = product.descricao
        if preco is not None:
            update_data["preco"] = product.preco
        if tamanho is not None:
            update_data["tamanho"] = product.tamanho
        if clube is not None:
            update_data["clube"] = product.clube
        if tipo is not None:
            update_data["tipo"] = product.tipo
        if estoque is not None:
            update_data["estoque"] = product.estoque
        if imagem_url is not None:
            update_data["imagem_url"] = product.imagem_url
        if ativo is not None:
            update_data["ativo"] = product.ativo

        if not update_data:
            return product

        updated = self.product_repository.update(product_id, update_data)
        if not updated:
            raise ValueError("Produto não encontrado")

        return updated
