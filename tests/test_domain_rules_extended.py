from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.entities.address import AddressEntity
from src.entities.cart import CartEntity
from src.entities.cart_item import CartItemEntity
from src.entities.coupon import CouponEntity
from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.entities.product import ProductEntity
from src.use_cases.coupon.apply_coupon import ApplyCouponUseCase
from src.use_cases.coupon.validate_coupon import ValidateCouponUseCase
from src.repositories.coupon_repository import CouponRepository


@pytest.mark.parametrize('field,value', [('rua', ''), ('numero', ''), ('bairro', ''), ('cidade', ''), ('estado', 'ABC'), ('cep', '123'), ('client_id', 0)])
def test_address_validation(field, value):
    data = dict(id=1, client_id=1, rua='Rua', numero='1', bairro='Centro', cidade='SP', estado='SP', cep='01001000')
    data[field] = value
    with pytest.raises(ValueError): AddressEntity(**data)


@pytest.mark.parametrize('field,value', [('nome', ''), ('category_id', 0), ('preco', 0), ('tamanho', ''), ('clube', ''), ('tipo', ''), ('estoque', -1)])
def test_product_validation(field, value):
    data = dict(id=1, category_id=1, nome='Shirt', preco=10, tamanho='M', clube='Club', tipo='Fan', estoque=2)
    data[field] = value
    with pytest.raises(ValueError): ProductEntity(**data)


@pytest.mark.parametrize('case', ['empty_code', 'zero', 'above_100', 'missing_date', 'inactive', 'expired', 'negative_total'])
def test_coupon_validation(case):
    data = dict(id=1, codigo='SAVE10', desconto=10, validade=date(2099, 1, 1))
    if case == 'empty_code': data['codigo'] = ' '
    if case == 'zero': data['desconto'] = 0
    if case == 'above_100': data['desconto'] = 101
    if case == 'missing_date': data['validade'] = None
    if case == 'inactive': data['ativo'] = False
    if case == 'expired': data['validade'] = date(2000, 1, 1)
    with pytest.raises(ValueError):
        CouponEntity(**data).calcular_desconto(Decimal('-1' if case == 'negative_total' else '100'))


def test_coupon_application_with_correct_validator(commerce_api, db_session):
    use_case = ApplyCouponUseCase(ValidateCouponUseCase(CouponRepository(db_session)))
    result = use_case.execute('SAVE10', 200)
    assert result.valido and result.desconto_aplicado == 20 and result.valor_final == 180
    with pytest.raises(ValueError): use_case.execute('SAVE10', -1)
    with pytest.raises(ValueError): use_case.execute('MISSING', 100)
    coupon = CouponEntity(1, ' save ', 10, datetime(2099, 1, 1))
    assert coupon.aplicar_desconto(Decimal('33.33')) == Decimal('30.00')
    coupon.desativar()
    assert not coupon.esta_valido()
    coupon.ativar()
    assert coupon.esta_valido()


def test_cart_domain_lifecycle():
    cart = CartEntity(1, 1)
    item = CartItemEntity(1, 2, 10, id=1)
    assert cart.esta_vazio()
    cart.adicionar_item(item)
    assert cart.buscar_item_por_produto(1) is item
    cart.atualizar_quantidade_item(1, 3)
    assert cart.calcular_total() == 30
    cart.remover_item(1)
    assert cart.esta_vazio() and cart.calcular_total() == 0
    assert cart.buscar_item_por_produto(1) is None
    with pytest.raises(ValueError): cart.remover_item(1)
    with pytest.raises(ValueError): cart.atualizar_quantidade_item(999, 1)
    item.ativar()
    cart.desativar()
    assert not cart.ativo and not item.ativo
    with pytest.raises(ValueError): cart.adicionar_item(CartItemEntity(1, 1, 10))
    with pytest.raises(ValueError): CartEntity(1, 0)


@pytest.mark.parametrize('cls', [CartItemEntity, OrderItemEntity])
def test_item_quantity_and_price_invariants(cls):
    for fields in [dict(product_id=0), dict(quantidade=0), dict(preco_unitario=-1)]:
        data = dict(product_id=1, quantidade=1, preco_unitario=10)
        data.update(fields)
        with pytest.raises(ValueError): cls(**data)
    item = cls(1, 2, 10)
    for method, value in [(item.atualizar_quantidade, 0), (item.atualizar_preco_unitario, -1)]:
        with pytest.raises(ValueError): method(value)
    item.atualizar_preco_unitario(12.5)
    assert item.calcular_subtotal() == 25
    item.desativar()
    assert item.subtotal() == 0


def test_order_totals_and_terminal_transitions():
    with pytest.raises(ValueError): OrderEntity(1)
    with pytest.raises(ValueError): OrderEntity(1, client_id=1, endereco_id=1, valor_total=-1)
    order = OrderEntity(1, client_id=1, endereco_id=1)
    with pytest.raises(ValueError): order.confirmar_pedido()
    order.adicionar_item(OrderItemEntity(1, 2, 10, id=1))
    order.frete = Decimal('5')
    order.aplicar_cupom(1, Decimal('50'))
    assert order.valor_total == 0
    with pytest.raises(ValueError): order.aplicar_cupom(1, Decimal('-1'))
    with pytest.raises(ValueError): order.remover_item(999)
    order.marcar_como_pago()
    order.alterar_status(OrderStatus.PREPARING)
    order.marcar_como_enviado()
    with pytest.raises(ValueError): order.cancelar_pedido()
    order.marcar_como_entregue()
    with pytest.raises(ValueError): order.alterar_status(OrderStatus.PAID)
