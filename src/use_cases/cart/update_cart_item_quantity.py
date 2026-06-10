from src.entities.cart import CartEntity
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository
from src.use_cases.cart_item.update_cart_item_quantity import (
    UpdateCartItemQuantityUseCase as UpdateCartItemQuantityItemUseCase,
)


class UpdateCartItemQuantityUseCase:
    def __init__(
        self,
        cart_repository: CartRepository,
        cart_item_repository: CartItemRepository,
    ):
        self.cart_repository = cart_repository
        self._update_cart_item = UpdateCartItemQuantityItemUseCase(
            cart_repository, cart_item_repository
        )

    def execute(self, cart_item_id: int, quantidade: int) -> CartEntity:
        item = self._update_cart_item.execute(cart_item_id, quantidade)

        updated_cart = self.cart_repository.get_by_id(item.cart_id)
        if not updated_cart:
            raise ValueError("Carrinho não encontrado")
        return updated_cart
