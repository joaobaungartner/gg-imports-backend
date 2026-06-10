from decimal import Decimal

from src.repositories.cart_repository import CartRepository


class CalculateCartTotalUseCase:
    def __init__(self, cart_repository: CartRepository):
        self.cart_repository = cart_repository

    def execute(self, cart_id: int) -> Decimal:
        cart = self.cart_repository.get_by_id(cart_id)
        if not cart:
            raise ValueError("Carrinho não encontrado")

        return cart.calcular_total()
