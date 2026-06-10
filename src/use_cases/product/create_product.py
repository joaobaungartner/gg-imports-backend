from decimal import Decimal

from src.entities.product import ProductEntity
from src.repositories.category_repository import CategoryRepository
from src.repositories.product_repository import ProductRepository


class CreateProductUseCase:
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
        category_id: int,
        nome: str,
        preco: float,
        tamanho: str,
        clube: str,
        tipo: str,
        descricao: str | None = None,
        estoque: int = 0,
        imagem_url: str | None = None,
        ativo: bool = True,
    ) -> ProductEntity:
        category = self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError("Categoria não encontrada")
        if not category.esta_ativa():
            raise ValueError("Categoria inativa")

        if estoque < 0:
            raise ValueError("Estoque inválido")

        product = ProductEntity(
            id=None,
            category_id=category_id,
            nome=nome,
            descricao=descricao,
            preco=Decimal(str(preco)),
            tamanho=tamanho,
            clube=clube,
            tipo=tipo,
            estoque=estoque,
            imagem_url=imagem_url,
            ativo=ativo,
        )

        return self.product_repository.create(product)
