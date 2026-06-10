from decimal import Decimal

from src.entities.cart_item import CartItemEntity
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository


class CreateCartItemUseCase:
    def __init__(
        self,
        cart_repository: CartRepository,
        cart_item_repository: CartItemRepository,
    ):
        self.cart_repository = cart_repository
        self.cart_item_repository = cart_item_repository
        # TODO: injetar ProductRepository quando disponível

    def _resolve_item_price(self, product_id: int) -> Decimal:
        # TODO: ProductRepository - validar produto ativo e obter preço atual
        return Decimal("0")

    def execute(
        self,
        cart_id: int,
        product_id: int,
        quantidade: int,
    ) -> CartItemEntity:
        cart = self.cart_repository.get_by_id(cart_id)
        if not cart:
            raise ValueError("Carrinho não encontrado")
        if not cart.ativo:
            raise ValueError("Carrinho inativo")

        if quantidade <= 0:
            raise ValueError("Quantidade inválida")

        # TODO: ProductRepository - validar se produto existe
        # TODO: ProductRepository - validar se produto está ativo
        # TODO: ProductRepository - validar estoque suficiente

        preco_unitario = self._resolve_item_price(product_id)

        existing_active = self.cart_item_repository.get_by_cart_and_product(
            cart_id, product_id
        )
        if existing_active:
            nova_quantidade = existing_active.quantidade + quantidade
            existing_active.atualizar_quantidade(nova_quantidade)
            updated = self.cart_item_repository.update_quantity(
                existing_active.id, nova_quantidade
            )
            if not updated:
                raise ValueError("Item do carrinho não encontrado")
            return updated

        existing_inactive = self.cart_item_repository.get_by_cart_and_product_any(
            cart_id, product_id
        )
        if existing_inactive and not existing_inactive.ativo:
            nova_quantidade = existing_inactive.quantidade + quantidade
            existing_inactive.ativar()
            existing_inactive.atualizar_quantidade(nova_quantidade)
            existing_inactive.atualizar_preco_unitario(preco_unitario)
            updated = self.cart_item_repository.update(
                existing_inactive.id,
                {
                    "ativo": True,
                    "quantidade": nova_quantidade,
                    "preco_unitario": preco_unitario,
                },
            )
            if not updated:
                raise ValueError("Item do carrinho não encontrado")
            return updated

        item = CartItemEntity(
            id=None,
            cart_id=cart_id,
            product_id=product_id,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
        )
        return self.cart_item_repository.create(item)
