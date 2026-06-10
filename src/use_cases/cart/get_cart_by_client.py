from src.entities.cart import CartEntity
from src.repositories.cart_repository import CartRepository
from src.repositories.client_repository import ClientRepository


class GetCartByClientUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        cart_repository: CartRepository,
    ):
        self.client_repository = client_repository
        self.cart_repository = cart_repository

    def execute(self, client_id: int) -> CartEntity:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        if not client.ativo:
            raise ValueError("Cliente inativo")

        cart = self.cart_repository.get_by_client_id(client_id)
        if cart:
            return cart

        cart = CartEntity(id=None, client_id=client_id)
        return self.cart_repository.create(cart)
