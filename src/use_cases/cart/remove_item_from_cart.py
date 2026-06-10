from src.entities.cart import CartEntity
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository
from src.use_cases.cart_item.remove_cart_item import RemoveCartItemUseCase


class RemoveItemFromCartUseCase:
    def __init__(
        self,
        cart_repository: CartRepository,
        cart_item_repository: CartItemRepository,
    ):
        self.cart_repository = cart_repository
        self._remove_cart_item = RemoveCartItemUseCase(
            cart_repository, cart_item_repository
        )

    def execute(self, cart_item_id: int) -> CartEntity:
        item = self._remove_cart_item.execute(cart_item_id)

        updated_cart = self.cart_repository.get_by_id(item.cart_id)
        if not updated_cart:
            raise ValueError("Carrinho não encontrado")
        return updated_cart
