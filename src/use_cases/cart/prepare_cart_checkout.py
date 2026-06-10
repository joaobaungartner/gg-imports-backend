from dataclasses import dataclass
from decimal import Decimal

from src.entities.cart_item import CartItemEntity
from src.repositories.cart_repository import CartRepository


@dataclass
class CartCheckoutResult:
    cart_id: int
    client_id: int
    itens: list[CartItemEntity]
    valor_total: Decimal
    valido_para_checkout: bool


class PrepareCartCheckoutUseCase:
    def __init__(self, cart_repository: CartRepository):
        self.cart_repository = cart_repository
        # TODO: injetar ProductRepository para validar estoque
        # TODO: integrar com CreateOrderUseCase após checkout

    def execute(self, cart_id: int) -> CartCheckoutResult:
        cart = self.cart_repository.get_by_id(cart_id)
        if not cart:
            raise ValueError("Carrinho não encontrado")
        if not cart.ativo:
            raise ValueError("Carrinho inativo")
        if cart.esta_vazio():
            raise ValueError("Carrinho vazio")

        itens_ativos = [item for item in cart.itens if item.ativo]

        # TODO: ProductRepository - validar estoque de cada produto
        # TODO: converter cada ItemCarrinho ativo em ItemPedido via CheckoutUseCase
        # TODO: CreateOrderUseCase - criar pedido a partir dos itens do carrinho
        # TODO: ClearCartUseCase - limpar carrinho após pedido criado com sucesso

        valor_total = cart.calcular_total()

        return CartCheckoutResult(
            cart_id=cart.id,
            client_id=cart.client_id,
            itens=itens_ativos,
            valor_total=valor_total,
            valido_para_checkout=True,
        )
