from src.entities.cart_item import CartItemEntity
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository


class UpdateCartItemQuantityUseCase:
    def __init__(
        self,
        cart_repository: CartRepository,
        cart_item_repository: CartItemRepository,
    ):
        self.cart_repository = cart_repository
        self.cart_item_repository = cart_item_repository
        # TODO: injetar ProductRepository para validar estoque

    def execute(self, cart_item_id: int, quantidade: int) -> CartItemEntity:
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

        if quantidade <= 0:
            raise ValueError("Quantidade inválida")

        # TODO: ProductRepository - validar estoque suficiente

        item.atualizar_quantidade(quantidade)
        updated_item = self.cart_item_repository.update_quantity(
            cart_item_id, quantidade
        )
        if not updated_item:
            raise ValueError("Item do carrinho não encontrado")

        # CalculateCartTotalUseCase pode ser chamado pelo caller quando necessário

        return updated_item
