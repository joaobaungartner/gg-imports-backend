from src.entities.cart_item import CartItemEntity
from src.repositories.cart_item_repository import CartItemRepository


class GetCartItemByIdUseCase:
    def __init__(self, cart_item_repository: CartItemRepository):
        self.cart_item_repository = cart_item_repository

    def execute(self, cart_item_id: int) -> CartItemEntity:
        item = self.cart_item_repository.get_by_id(cart_item_id)
        if not item:
            raise ValueError("Item do carrinho não encontrado")
        return item
