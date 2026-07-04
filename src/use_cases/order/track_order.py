import re

from src.entities.order import OrderEntity
from src.repositories.order_repository import OrderRepository


class TrackOrderUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    @staticmethod
    def _normalize_digits(value: str) -> str:
        return re.sub(r"\D", "", value)

    @staticmethod
    def _matches_identifier(order: OrderEntity, identifier: str) -> bool:
        normalized = identifier.strip()
        if not normalized:
            return False

        email = (order.customer_email or "").strip().lower()
        if email and normalized.lower() == email:
            return True

        cpf = TrackOrderUseCase._normalize_digits(order.customer_cpf or "")
        identifier_digits = TrackOrderUseCase._normalize_digits(normalized)
        if cpf and identifier_digits and cpf == identifier_digits:
            return True

        phone = TrackOrderUseCase._normalize_digits(order.customer_phone or "")
        if phone and identifier_digits and phone == identifier_digits:
            return True

        if phone and identifier_digits and phone.endswith(identifier_digits):
            return True

        return False

    def execute(self, order_id: int, identifier: str) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order or not order.ativo:
            raise ValueError("Pedido não encontrado")

        if not self._matches_identifier(order, identifier):
            raise ValueError("Pedido não encontrado")

        return order
