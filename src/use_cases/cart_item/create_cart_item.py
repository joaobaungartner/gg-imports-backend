from decimal import Decimal

from src.entities.cart_item import CartItemEntity
from src.repositories.cart_item_repository import CartItemRepository
from src.repositories.cart_repository import CartRepository
from src.repositories.product_repository import ProductRepository
from src.use_cases.product.check_product_availability import (
    CheckProductAvailabilityUseCase,
)


class CreateCartItemUseCase:
    def __init__(
        self,
        cart_repository: CartRepository,
        cart_item_repository: CartItemRepository,
        product_repository: ProductRepository,
    ):
        self.cart_repository = cart_repository
        self.cart_item_repository = cart_item_repository
        self.product_repository = product_repository
        self._check_availability = CheckProductAvailabilityUseCase(
            product_repository
        )

    def _resolve_item_price(
        self, product_id: int, quantidade: int
    ) -> Decimal:
        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")
        if not product.ativo:
            raise ValueError("Produto inativo")

        availability = self._check_availability.execute(product_id, quantidade)
        if not availability.disponivel:
            raise ValueError("Estoque insuficiente")

        return product.preco

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

        existing_active = self.cart_item_repository.get_by_cart_and_product(
            cart_id, product_id
        )
        existing_inactive = self.cart_item_repository.get_by_cart_and_product_any(
            cart_id, product_id
        )

        quantidade_total = quantidade
        if existing_active:
            quantidade_total = existing_active.quantidade + quantidade
        elif existing_inactive and not existing_inactive.ativo:
            quantidade_total = existing_inactive.quantidade + quantidade

        preco_unitario = self._resolve_item_price(product_id, quantidade_total)

        if existing_active:
            existing_active.atualizar_quantidade(quantidade_total)
            updated = self.cart_item_repository.update_quantity(
                existing_active.id, quantidade_total
            )
            if not updated:
                raise ValueError("Item do carrinho não encontrado")
            return updated

        if existing_inactive and not existing_inactive.ativo:
            existing_inactive.ativar()
            existing_inactive.atualizar_quantidade(quantidade_total)
            existing_inactive.atualizar_preco_unitario(preco_unitario)
            updated = self.cart_item_repository.update(
                existing_inactive.id,
                {
                    "ativo": True,
                    "quantidade": quantidade_total,
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
