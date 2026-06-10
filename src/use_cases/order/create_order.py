from decimal import Decimal

from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.repositories.client_repository import ClientRepository
from src.repositories.coupon_repository import CouponRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.use_cases.address.validate_address_for_order import (
    ValidateAddressForOrderUseCase,
)
from src.use_cases.product.check_product_availability import (
    CheckProductAvailabilityUseCase,
)


class CreateOrderUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        order_repository: OrderRepository,
        validate_address_use_case: ValidateAddressForOrderUseCase,
        coupon_repository: CouponRepository,
        product_repository: ProductRepository,
    ):
        self.client_repository = client_repository
        self.order_repository = order_repository
        self.validate_address_use_case = validate_address_use_case
        self.coupon_repository = coupon_repository
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

    def _resolve_coupon_discount(
        self, cupom_id: int | None, subtotal: Decimal
    ) -> Decimal:
        if cupom_id is None:
            return Decimal("0")
        coupon = self.coupon_repository.get_by_id(cupom_id)
        if not coupon:
            raise ValueError("Cupom não encontrado")
        desconto_aplicado, _ = coupon.calcular_desconto(subtotal)
        return desconto_aplicado

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

        self.validate_address_use_case.execute(endereco_id, client_id)

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

            preco_unitario = self._resolve_item_price(product_id, quantidade)

            order_item = OrderItemEntity(
                product_id=product_id,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
            )
            order.adicionar_item(order_item)

        subtotal = sum(
            (item.subtotal() for item in order.itens), Decimal("0")
        )
        desconto = self._resolve_coupon_discount(cupom_id, subtotal)
        if cupom_id is not None:
            order.aplicar_cupom(cupom_id, desconto)

        order.calcular_total()
        return self.order_repository.create(order)
