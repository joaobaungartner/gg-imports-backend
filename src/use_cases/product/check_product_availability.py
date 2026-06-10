from dataclasses import dataclass

from src.repositories.product_repository import ProductRepository


@dataclass
class ProductAvailabilityResult:
    product_id: int
    disponivel: bool
    estoque_atual: int
    quantidade_solicitada: int


class CheckProductAvailabilityUseCase:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def execute(
        self, product_id: int, quantidade: int
    ) -> ProductAvailabilityResult:
        if quantidade <= 0:
            raise ValueError("Quantidade inválida")

        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")

        if not product.ativo:
            raise ValueError("Produto inativo")

        disponivel = product.verificar_estoque_disponivel(quantidade)

        return ProductAvailabilityResult(
            product_id=product_id,
            disponivel=disponivel,
            estoque_atual=product.estoque,
            quantidade_solicitada=quantidade,
        )
