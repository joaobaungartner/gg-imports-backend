from decimal import Decimal

from src.entities.payment import PaymentEntity, PaymentMethod, PaymentStatus
from src.repositories.order_repository import OrderRepository
from src.repositories.payment_repository import PaymentRepository


class CreatePaymentUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        payment_repository: PaymentRepository,
    ):
        self.order_repository = order_repository
        self.payment_repository = payment_repository

    def execute(
        self,
        order_id: int,
        metodo: str,
        valor: float | Decimal,
    ) -> PaymentEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")
        if not order.ativo:
            raise ValueError("Pedido não encontrado")

        existing_payment = self.payment_repository.get_by_order_id(order_id)
        if existing_payment and existing_payment.ativo:
            raise ValueError("Pedido já possui pagamento")

        valor_decimal = (
            Decimal(str(valor)) if not isinstance(valor, Decimal) else valor
        )
        if valor_decimal <= 0:
            raise ValueError("Valor do pagamento inválido")

        if valor_decimal != order.valor_total:
            raise ValueError("Valor do pagamento inválido")

        try:
            payment_method = PaymentMethod(metodo)
        except ValueError as exc:
            raise ValueError("Método de pagamento inválido") from exc

        payment = PaymentEntity(
            id=None,
            order_id=order_id,
            metodo=payment_method,
            valor=valor_decimal,
            status=PaymentStatus.PENDING,
        )

        created_payment = self.payment_repository.create(payment)

        self.order_repository.update(
            order_id, {"pagamento_id": created_payment.id}
        )

        return created_payment
