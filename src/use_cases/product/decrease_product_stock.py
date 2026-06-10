from src.entities.product import ProductEntity
from src.repositories.product_repository import ProductRepository


class DecreaseProductStockUseCase:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def execute(self, product_id: int, quantidade: int) -> ProductEntity:
        if quantidade <= 0:
            raise ValueError("Estoque inválido")

        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")

        if not product.verificar_estoque_disponivel(quantidade):
            raise ValueError("Estoque insuficiente")

        updated = self.product_repository.decrease_stock(product_id, quantidade)
        if not updated:
            raise ValueError("Produto não encontrado")

        return updated
