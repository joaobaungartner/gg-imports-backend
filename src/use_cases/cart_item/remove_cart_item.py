from src.entities.cart_item import CartItemEntity
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository


class RemoveCartItemUseCase:
    def __init__(
        self,
        cart_repository: CartRepository,
        cart_item_repository: CartItemRepository,
    ):
        self.cart_repository = cart_repository
        self.cart_item_repository = cart_item_repository

    def execute(self, cart_item_id: int) -> CartItemEntity:
        item = self.cart_item_repository.get_by_id(cart_item_id)
        if not item:
            raise ValueError("Item do carrinho não encontrado")
        if not item.ativo:
            raise ValueError("Item do carrinho não encontrado")

        cart = self.cart_repository.get_by_id(item.cart_id)
        if not cart:
            raise ValueError("Carrinho não encontrado")
        if not cart.ativo:
            raise ValueError("Carrinho inativo")

        deactivated = self.cart_item_repository.deactivate(cart_item_id)
        if not deactivated:
            raise ValueError("Item do carrinho não encontrado")

        return deactivated
