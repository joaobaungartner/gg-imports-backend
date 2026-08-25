"""Garante que dados comerciais do pedido venham do catálogo persistido."""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.entities.product import ProductEntity
from src.schemas.order_schema import CheckoutOrderItemCreate
from src.use_cases.order.create_checkout_order import CreateCheckoutOrderUseCase


class ProductRepositoryStub:
    def __init__(self, product: ProductEntity):
        self.product = product

    def get_by_id(self, product_id: int):
        return self.product if product_id == self.product.id else None

    def reserve_stock(self, product_id: int, quantity: int):
        if product_id != self.product.id or self.product.estoque < quantity:
            raise ValueError("Estoque insuficiente")
        self.product.estoque -= quantity


class ClientRepositoryStub:
    def get_by_user_id(self, user_id: int):
        return SimpleNamespace(client_id=7) if user_id == 10 else None


class OrderRepositorySpy:
    def __init__(self):
        self.created = None
        self.db = SimpleNamespace(commit=lambda: None, rollback=lambda: None)

    def create(self, order, *, commit=True):
        self.created = order
        order.id = 99
        return order

    def get_by_id(self, order_id):
        return self.created if self.created and self.created.id == order_id else None


def make_product(*, stock: int = 5) -> ProductEntity:
    return ProductEntity(
        id=42,
        category_id=1,
        nome="Camisa oficial",
        preco=Decimal("299.90"),
        tamanho="G",
        clube="GG FC",
        tipo="Torcedor",
        estoque=stock,
        imagem_url="https://cdn.example.com/camisa.jpg",
        ativo=True,
    )


def create_order(items: list[dict], *, stock: int = 5):
    product_repository = ProductRepositoryStub(make_product(stock=stock))
    order_repository = OrderRepositorySpy()
    use_case = CreateCheckoutOrderUseCase(
        order_repository,
        product_repository,
        ClientRepositoryStub(),
    )
    return use_case.execute(
        customer_name="Cliente",
        customer_email="cliente@example.com",
        customer_phone="11999999999",
        shipping_address={
            "cep": "01001000",
            "street": "Praça da Sé",
            "number": "1",
            "neighborhood": "Sé",
            "city": "São Paulo",
            "state": "SP",
        },
        payment_method="PIX",
        items=items,
        authenticated_user_id=10,
        shipping_method="ENTREGA",
        frete=Decimal("18.00") + Decimal("8.00") * (sum(
            item["quantity"] for item in items
        ) - 1),
    )


def test_checkout_schema_rejects_client_supplied_commercial_data():
    with pytest.raises(ValidationError):
        CheckoutOrderItemCreate.model_validate(
            {
                "product_id": 42,
                "quantity": 1,
                "unit_price": "1.00",
                "name": "Produto adulterado",
                "size": "X",
                "image_url": "https://attacker.example/fake.jpg",
            }
        )


def test_checkout_uses_product_data_and_price_from_repository():
    order = create_order([{"product_id": 42, "quantity": 2}])

    assert order.subtotal == Decimal("599.80")
    assert order.valor_total == Decimal("625.80")
    assert len(order.itens) == 1
    assert order.itens[0].preco_unitario == Decimal("299.90")
    assert order.itens[0].nome_produto == "Camisa oficial"
    assert order.itens[0].tamanho == "G"
    assert order.itens[0].imagem_url == "https://cdn.example.com/camisa.jpg"
    assert order.estoque_reservado is True
    assert order.reserva_expira_em is not None


def test_duplicate_product_lines_are_checked_against_total_quantity():
    with pytest.raises(ValueError, match="Estoque insuficiente"):
        create_order(
            [
                {"product_id": 42, "quantity": 3},
                {"product_id": 42, "quantity": 3},
            ],
            stock=5,
        )
