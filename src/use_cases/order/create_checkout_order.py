from decimal import Decimal
from datetime import datetime, timedelta

from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.entities.product import ProductEntity
from src.repositories.client_repository import ClientRepository
from src.repositories.coupon_repository import CouponRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.notification_repository import NotificationRepository
from src.services.notification_service import NotificationService
from src.use_cases.product.check_product_availability import (
    CheckProductAvailabilityUseCase,
)
from src.use_cases.shipping.calculate_shipping import CalculateShippingUseCase


class CreateCheckoutOrderUseCase:
    PIX_RESERVATION_MINUTES = 30
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        client_repository: ClientRepository | None = None,
        calculate_shipping_use_case: CalculateShippingUseCase | None = None,
        coupon_repository: CouponRepository | None = None,
        notification_repository: NotificationRepository | None = None,
    ):
        self.order_repository = order_repository
        self.product_repository = product_repository
        self.client_repository = client_repository
        self._check_availability = CheckProductAvailabilityUseCase(
            product_repository
        )
        self._calculate_shipping = calculate_shipping_use_case or CalculateShippingUseCase()
        self.coupon_repository = coupon_repository
        self.notification_repository = notification_repository

    @staticmethod
    def _normalize_cep(cep: str) -> str:
        return cep.replace("-", "").strip()

    def _get_available_product(
        self, product_id: int, quantity: int
    ) -> ProductEntity:
        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise ValueError("Produto não encontrado")
        if not product.ativo:
            raise ValueError(f"Produto indisponível: {product.nome}")

        availability = self._check_availability.execute(product_id, quantity)
        if not availability.disponivel:
            raise ValueError(f"Estoque insuficiente para {product.nome}")
        return product

    @staticmethod
    def _consolidate_items(items: list[dict]) -> dict[int, int]:
        quantities_by_product: dict[int, int] = {}
        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            quantities_by_product[product_id] = (
                quantities_by_product.get(product_id, 0) + quantity
            )
        return quantities_by_product

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
        coupon_code: str | None = None,
    ) -> OrderEntity:
        if not authenticated_user_id:
            raise ValueError("Usuário não autenticado")

        if not items:
            raise ValueError("Pedido deve conter ao menos um item")

        # Recolhe reservas PIX vencidas antes de disputar o estoque. O endpoint
        # administrativo equivalente também pode ser executado periodicamente.
        if hasattr(self.order_repository, "list_expired_reservations"):
            from src.repositories.order_status_history_repository import (
                OrderStatusHistoryRepository,
            )
            from src.use_cases.order.expire_stock_reservations import (
                ExpireStockReservationsUseCase,
            )

            ExpireStockReservationsUseCase(
                self.order_repository,
                self.product_repository,
                OrderStatusHistoryRepository(self.order_repository.db),
            ).execute()

        quantities_by_product = self._consolidate_items(items)
        products = {
            product_id: self._get_available_product(product_id, quantity)
            for product_id, quantity in quantities_by_product.items()
        }

        if not self.client_repository:
            raise ValueError("Cliente não encontrado")

        client = self.client_repository.get_by_user_id(authenticated_user_id)
        if not client:
            raise ValueError("Cliente não encontrado")

        normalized_cep = self._normalize_cep(shipping_address["cep"])
        shipping_state = shipping_address["state"].strip().upper()
        item_count = sum(quantities_by_product.values())
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
            estoque_reservado=True,
            # Nenhum checkout pendente pode prender estoque indefinidamente.
            reserva_expira_em=datetime.utcnow()
            + timedelta(minutes=self.PIX_RESERVATION_MINUTES),
            frete=frete_calculado,
        )

        for product_id, quantity in quantities_by_product.items():
            product = products[product_id]
            order_item = OrderItemEntity(
                product_id=product.id,
                quantidade=quantity,
                preco_unitario=product.preco,
                nome_produto=product.nome,
                imagem_url=product.imagem_url,
                tamanho=product.tamanho,
            )
            order.adicionar_item(order_item)

        if coupon_code:
            if not self.coupon_repository:
                raise ValueError("Cupom indisponível")
            coupon = self.coupon_repository.get_by_code(coupon_code.strip().upper())
            if not coupon:
                raise ValueError("Cupom não encontrado")
            discount, _ = coupon.calcular_desconto(order.subtotal)
            order.aplicar_cupom(coupon.id, discount)

        order.calcular_total()
        try:
            for product_id, quantity in quantities_by_product.items():
                self.product_repository.reserve_stock(product_id, quantity)
            created = self.order_repository.create(order, commit=False)
            if self.notification_repository:
                NotificationService(self.notification_repository).email(
                    "ORDER_CREATED", order.customer_email,
                    f"Pedido #{created.id} recebido — GG Imports",
                    f"Recebemos seu pedido #{created.id}. Total: R$ {order.valor_total}.",
                    commit=False,
                )
            self.order_repository.db.commit()
            return self.order_repository.get_by_id(created.id) or created
        except Exception:
            self.order_repository.db.rollback()
            raise
