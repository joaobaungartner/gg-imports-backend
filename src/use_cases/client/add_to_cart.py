from src.entities.cart import CartEntity
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository
from src.repositories.client_repository import ClientRepository
from src.use_cases.cart.add_item_to_cart import AddItemToCartUseCase
from src.use_cases.cart.get_cart_by_client import GetCartByClientUseCase


class AddToCartUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        cart_repository: CartRepository,
        cart_item_repository: CartItemRepository,
    ):
        self.client_repository = client_repository
        self._get_cart_by_client = GetCartByClientUseCase(
            client_repository, cart_repository
        )
        self._add_item_to_cart = AddItemToCartUseCase(
            cart_repository, cart_item_repository
        )

    def execute(
        self, client_id: int, produto_id: int, quantidade: int
    ) -> CartEntity:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")

        client.adicionar_ao_carrinho(produto_id, quantidade)

        cart = self._get_cart_by_client.execute(client_id)
        return self._add_item_to_cart.execute(cart.id, produto_id, quantidade)
