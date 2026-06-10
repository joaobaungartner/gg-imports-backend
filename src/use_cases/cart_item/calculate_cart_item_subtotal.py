from decimal import Decimal

from src.repositories.cart_item_repository import CartItemRepository


class CalculateCartItemSubtotalUseCase:
    def __init__(self, cart_item_repository: CartItemRepository):
        self.cart_item_repository = cart_item_repository

    def execute(self, cart_item_id: int) -> Decimal:
        item = self.cart_item_repository.get_by_id(cart_item_id)
        if not item:
            raise ValueError("Item do carrinho não encontrado")

        return item.calcular_subtotal()
