from decimal import Decimal

from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.repositories.client_repository import ClientRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.use_cases.product.check_product_availability import (
    CheckProductAvailabilityUseCase,
)
from src.use_cases.shipping.calculate_shipping import CalculateShippingUseCase


class CreateCheckoutOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        client_repository: ClientRepository | None = None,
        calculate_shipping_use_case: CalculateShippingUseCase | None = None,
    ):
        self.order_repository = order_repository
        self.product_repository = product_repository
        self.client_repository = client_repository
        self._check_availability = CheckProductAvailabilityUseCase(
            product_repository
        )
        self._calculate_shipping = calculate_shipping_use_case or CalculateShippingUseCase()

    @staticmethod
    def _normalize_cep(cep: str) -> str:
        return cep.replace("-", "").strip()

    def _validate_item(self, item_data: dict) -> None:
        product_id = item_data["product_id"]
        quantity = item_data["quantity"]

        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")
        if not product.ativo:
            raise ValueError(f"Produto indisponível: {item_data['name']}")

        availability = self._check_availability.execute(product_id, quantity)
        if not availability.disponivel:
            raise ValueError(f"Estoque insuficiente para {item_data['name']}")

    def _resolve_frete(
        self,
        cep: str,
        state: str,
        shipping_method: str,
        item_count: int,
        frete_informado: Decimal,
    ) -> Decimal:
        quote = self._calculate_shipping.execute(
            cep=cep,
            shipping_method=shipping_method,
            item_count=item_count,
            state=state,
        )
        if quote.frete != frete_informado:
            raise ValueError("Valor de frete inválido. Atualize a cotação e tente novamente.")
        return quote.frete

    def execute(
        self,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        shipping_address: dict,
        payment_method: str,
        items: list[dict],
        authenticated_user_id: int,
        shipping_method: str = "ENTREGA",
        customer_cpf: str | None = None,
        frete: Decimal | None = None,
    ) -> OrderEntity:
        if not authenticated_user_id:
            raise ValueError("Usuário não autenticado")

        if not items:
            raise ValueError("Pedido deve conter ao menos um item")

        for item_data in items:
            self._validate_item(item_data)

        if not self.client_repository:
            raise ValueError("Cliente não encontrado")

        client = self.client_repository.get_by_user_id(authenticated_user_id)
        if not client:
            raise ValueError("Cliente não encontrado")

        normalized_cep = self._normalize_cep(shipping_address["cep"])
        shipping_state = shipping_address["state"].strip().upper()
        item_count = sum(item["quantity"] for item in items)
        frete_informado = frete if frete is not None else Decimal("0")
        frete_calculado = self._resolve_frete(
            normalized_cep,
            shipping_state,
            shipping_method,
            item_count,
            frete_informado,
        )

        order = OrderEntity(
            id=None,
            client_id=client.client_id,
            endereco_id=None,
            customer_name=customer_name.strip(),
            customer_email=customer_email.strip().lower(),
            customer_phone=customer_phone.strip(),
            customer_cpf=customer_cpf,
            shipping_cep=normalized_cep,
            shipping_street=shipping_address["street"].strip(),
            shipping_number=shipping_address["number"].strip(),
            shipping_complement=(shipping_address.get("complement") or "").strip() or None,
            shipping_neighborhood=shipping_address["neighborhood"].strip(),
            shipping_city=shipping_address["city"].strip(),
            shipping_state=shipping_state,
            shipping_method=shipping_method,
            payment_method=payment_method.upper(),
            status=OrderStatus.PENDING_PAYMENT,
            frete=frete_calculado,
        )

        for item_data in items:
            unit_price = Decimal(str(item_data["unit_price"]))
            order_item = OrderItemEntity(
                product_id=item_data["product_id"],
                quantidade=item_data["quantity"],
                preco_unitario=unit_price,
                nome_produto=item_data["name"],
                imagem_url=item_data.get("image_url"),
                tamanho=item_data["size"],
            )
            order.adicionar_item(order_item)

        order.calcular_total()
        return self.order_repository.create(order)
