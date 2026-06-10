from src.entities.cart_item import CartItemEntity
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository


class GetCartItemsByCartUseCase:
    def __init__(
        self,
        cart_repository: CartRepository,
        cart_item_repository: CartItemRepository,
    ):
        self.cart_repository = cart_repository
        self.cart_item_repository = cart_item_repository

    def execute(self, cart_id: int) -> list[CartItemEntity]:
        cart = self.cart_repository.get_by_id(cart_id)
        if not cart:
            raise ValueError("Carrinho não encontrado")

        itens = self.cart_item_repository.get_by_cart_id(cart_id)
        return [item for item in itens if item.ativo]
