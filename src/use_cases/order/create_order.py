from decimal import Decimal

from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.repositories.client_repository import ClientRepository
from src.repositories.order_repository import OrderRepository


class CreateOrderUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        order_repository: OrderRepository,
    ):
        self.client_repository = client_repository
        self.order_repository = order_repository
        # TODO: injetar AddressRepository quando disponível
        # TODO: injetar ProductRepository quando disponível
        # TODO: injetar CouponRepository quando disponível

    def _resolve_item_price(self, product_id: int) -> Decimal:
        # TODO: integrar ProductRepository para validar produto e obter preço
        # Exemplo futuro:
        # product = self.product_repository.get_by_id(product_id)
        # if not product or not product.ativo:
        #     raise ValueError("Produto não encontrado")
        # return product.preco
        return Decimal("0")

    def _resolve_coupon_discount(self, cupom_id: int | None) -> Decimal:
        if cupom_id is None:
            return Decimal("0")
        # TODO: integrar CouponRepository para validar cupom e obter desconto
        # Exemplo futuro:
        # coupon = self.coupon_repository.get_by_id(cupom_id)
        # if not coupon or not coupon.ativo:
        #     raise ValueError("Cupom inválido")
        # return coupon.desconto
        return Decimal("0")

    def execute(
        self,
        client_id: int,
        endereco_id: int,
        itens: list[dict],
        cupom_id: int | None = None,
    ) -> OrderEntity:
        client = self.client_repository.get_by_id(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        if not client.ativo:
            raise ValueError("Cliente inativo")

        # TODO: integrar AddressRepository para validar endereco_id
        # Exemplo futuro:
        # address = self.address_repository.get_by_id(endereco_id)
        # if not address:
        #     raise ValueError("Endereço não encontrado")

        order = OrderEntity(
            id=None,
            client_id=client_id,
            endereco_id=endereco_id,
            status=OrderStatus.PENDING,
            cupom_id=cupom_id,
        )

        for item_data in itens:
            product_id = item_data["product_id"]
            quantidade = item_data["quantidade"]

            # TODO: ProductRepository - validar produto ativo e estoque
            preco_unitario = self._resolve_item_price(product_id)

            order_item = OrderItemEntity(
                product_id=product_id,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
            )
            order.adicionar_item(order_item)

        desconto = self._resolve_coupon_discount(cupom_id)
        if cupom_id is not None:
            order.aplicar_cupom(cupom_id, desconto)

        order.calcular_total()
        return self.order_repository.create(order)
