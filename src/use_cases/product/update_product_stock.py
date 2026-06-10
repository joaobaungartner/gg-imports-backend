from src.entities.product import ProductEntity
from src.repositories.product_repository import ProductRepository


class UpdateProductStockUseCase:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(self, product_id: int, estoque: int) -> ProductEntity:
        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")

        product.atualizar_estoque(estoque)

        updated = self.product_repository.update_stock(product_id, product.estoque)
        if not updated:
            raise ValueError("Produto não encontrado")

        return updated
