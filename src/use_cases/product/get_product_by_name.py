from src.entities.product import ProductEntity
from src.repositories.product_repository import ProductRepository


class GetProductByNameUseCase:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def execute(self, nome: str) -> ProductEntity:
        nome_normalizado = nome.strip()
        if not nome_normalizado:
            raise ValueError("Nome do produto é obrigatório")

        product = self.product_repository.get_by_name(nome_normalizado)
        if not product:
            raise ValueError("Produto não encontrado")
        return product
