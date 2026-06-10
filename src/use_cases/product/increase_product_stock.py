from src.entities.product import ProductEntity
from src.repositories.product_repository import ProductRepository


class IncreaseProductStockUseCase:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(self, product_id: int, quantidade: int) -> ProductEntity:
        if quantidade <= 0:
            raise ValueError("Estoque inválido")

        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")

        updated = self.product_repository.increase_stock(product_id, quantidade)
        if not updated:
            raise ValueError("Produto não encontrado")

        return updated
