from src.entities.order import OrderEntity
from src.repositories.client_repository import ClientRepository
from src.repositories.order_repository import OrderRepository
from src.use_cases.address.validate_address_for_order import (
    ValidateAddressForOrderUseCase,
)


class ConfirmOrderUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        order_repository: OrderRepository,
        validate_address_use_case: ValidateAddressForOrderUseCase,
    ):
        self.client_repository = client_repository
        self.order_repository = order_repository
        self.validate_address_use_case = validate_address_use_case
        # TODO: injetar ProductRepository quando disponível

    def execute(self, order_id: int) -> OrderEntity:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Pedido não encontrado")

        client = self.client_repository.get_by_id(order.client_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        if not client.ativo:
            raise ValueError("Cliente inativo")

        self.validate_address_use_case.execute(order.endereco_id, order.client_id)

        # TODO: integrar ProductRepository para validar estoque dos itens
        # Exemplo futuro:
        # for item in order.itens:
        #     product = self.product_repository.get_by_id(item.product_id)
        #     if not product or product.estoque < item.quantidade:
        #         raise ValueError("Estoque insuficiente")

        order.confirmar_pedido()

        # TODO: integrar ProductRepository para baixa de estoque

        updated_order = self.order_repository.update_status(
            order_id, order.status.value
        )
        if not updated_order:
            raise ValueError("Pedido não encontrado")

        return updated_order
