from src.entities.cart import CartEntity
from src.repositories.cart_repository import CartRepository


class ClearCartUseCase:
    def __init__(self, cart_repository: CartRepository):
        self.cart_repository = cart_repository

    def execute(self, cart_id: int) -> CartEntity:
        cart = self.cart_repository.get_by_id(cart_id)
        if not cart:
            raise ValueError("Carrinho não encontrado")
        if not cart.ativo:
            raise ValueError("Carrinho inativo")

        cleared_cart = self.cart_repository.clear_cart(cart_id)
        if not cleared_cart:
            raise ValueError("Carrinho não encontrado")
        return cleared_cart
