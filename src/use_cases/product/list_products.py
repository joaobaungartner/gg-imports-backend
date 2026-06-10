from src.entities.product import ProductEntity
from src.repositories.product_repository import ProductRepository


class ListProductsUseCase:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def execute(
        self,
        ativo: bool | None = None,
        category_id: int | None = None,
        clube: str | None = None,
        tipo: str | None = None,
        tamanho: str | None = None,
    ) -> list[ProductEntity]:
        products = self.product_repository.list_all()

        if category_id is not None:
            products = [p for p in products if p.category_id == category_id]
        if clube is not None:
            clube_normalizado = clube.strip()
            products = [p for p in products if p.clube == clube_normalizado]
        if tipo is not None:
            tipo_normalizado = tipo.strip()
            products = [p for p in products if p.tipo == tipo_normalizado]
        if tamanho is not None:
            tamanho_normalizado = tamanho.strip()
            products = [p for p in products if p.tamanho == tamanho_normalizado]
        if ativo is True:
            products = [p for p in products if p.ativo]
        elif ativo is False:
            products = [p for p in products if not p.ativo]

        return products
