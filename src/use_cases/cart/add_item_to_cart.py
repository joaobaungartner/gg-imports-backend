from src.entities.cart import CartEntity
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository
from src.use_cases.cart_item.create_cart_item import CreateCartItemUseCase


class AddItemToCartUseCase:
    def __init__(
        self,
        cart_repository: CartRepository,
        cart_item_repository: CartItemRepository,
    ):
        self.cart_repository = cart_repository
        self._create_cart_item = CreateCartItemUseCase(
            cart_repository, cart_item_repository
        )

    def execute(
        self,
        cart_id: int,
        product_id: int,
        quantidade: int,
    ) -> CartEntity:
        self._create_cart_item.execute(cart_id, product_id, quantidade)

        updated_cart = self.cart_repository.get_by_id(cart_id)
        if not updated_cart:
            raise ValueError("Carrinho não encontrado")
        return updated_cart
