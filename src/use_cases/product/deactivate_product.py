from src.entities.product import ProductEntity
from src.repositories.product_repository import ProductRepository


class DeactivateProductUseCase:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository
        # TODO: validar permissão de Admin quando middleware existir

    def execute(self, product_id: int) -> ProductEntity:
        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")

        deactivated = self.product_repository.deactivate(product_id)
        if not deactivated:
            raise ValueError("Produto não encontrado")

        return deactivated
