from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.entities.order import OrderEntity, OrderStatus
from src.entities.order_item import OrderItemEntity
from src.entities.product import ProductEntity
from src.use_cases.order.update_order_status import UpdateOrderStatusUseCase
from src.use_cases.order.update_admin_order_status import UpdateAdminOrderStatusUseCase
from src.use_cases.order.create_order import CreateOrderUseCase
from src.use_cases.order.confirm_order import ConfirmOrderUseCase
from src.use_cases.order.cancel_order import CancelOrderUseCase
from src.use_cases.order.calculate_order_total import CalculateOrderTotalUseCase
from src.use_cases.order.apply_coupon_to_order import ApplyCouponToOrderUseCase
from src.use_cases.order.remove_order_item import RemoveOrderItemUseCase
from src.use_cases.order.track_order import TrackOrderUseCase
from src.use_cases.order.update_admin_order_notes import UpdateAdminOrderNotesUseCase
from src.use_cases.order_item.create_order_item import CreateOrderItemUseCase
from src.use_cases.order_item.update_order_item_quantity import UpdateOrderItemQuantityUseCase
from src.use_cases.order_item.remove_order_item import RemoveOrderItemUseCase as DeactivateItem
from src.use_cases.product.increase_product_stock import IncreaseProductStockUseCase
from src.use_cases.product.decrease_product_stock import DecreaseProductStockUseCase
from src.use_cases.product.update_product_stock import UpdateProductStockUseCase
from src.use_cases.product.check_product_availability import CheckProductAvailabilityUseCase


@pytest.fixture
def context():
    order = OrderEntity(1, client_id=1, endereco_id=1, itens=[OrderItemEntity(1, 2, 10, id=1, order_id=1)])
    order.calcular_total()
    product = ProductEntity(1, 1, 'Shirt', 10, 'M', 'Club', 'Fan', estoque=5)
    orders, products, items, clients, coupons, history = [Mock() for _ in range(6)]
    orders.get_by_id.return_value = order
    orders.get_by_id_for_update.return_value = order
    orders.update.return_value = order
    products.get_by_id.return_value = product
    items.get_by_id.return_value = order.itens[0]
    clients.get_by_id.return_value = SimpleNamespace(ativo=True)
    return SimpleNamespace(order=order, product=product, orders=orders, products=products,
                           items=items, clients=clients, coupons=coupons, history=history)


@pytest.mark.parametrize('cls', [UpdateOrderStatusUseCase, UpdateAdminOrderStatusUseCase])
@pytest.mark.parametrize('case', ['valid', 'missing', 'invalid', 'same', 'canceled', 'terminal', 'forced', 'rollback', 'updated_missing', 'cancel'])
def test_status_rules(context, cls, case):
    c = context
    status, force = 'PAID', False
    if case == 'missing': c.orders.get_by_id.return_value = None
    if case == 'invalid': status = 'unknown'
    if case == 'same': status = 'PENDING_PAYMENT'
    if case == 'canceled': c.order.status = OrderStatus.CANCELED
    if case in ('terminal', 'forced'): c.order.status = OrderStatus.DELIVERED
    if case == 'forced': force = True
    if case == 'rollback': c.history.create.side_effect = RuntimeError('database failure')
    if case == 'updated_missing': c.orders.get_by_id.side_effect = [c.order, None]
    if case == 'cancel': status = 'CANCELED'
    use_case = cls(c.orders, c.history, c.products)
    if case in ('valid', 'forced', 'cancel'):
        assert use_case.execute(1, status, 7, note='Reviewed', force=force) is c.order
        assert c.order.status.value == status
        c.orders.db.commit.assert_called_once()
        assert c.history.create.call_args.kwargs['changed_by_user_id'] == 7
    else:
        with pytest.raises(RuntimeError if case == 'rollback' else ValueError):
            use_case.execute(1, status, 7, force=force)
        if case == 'rollback': c.orders.db.rollback.assert_called_once()


@pytest.mark.parametrize('case', ['valid', 'client_missing', 'client_inactive', 'product_missing', 'product_inactive', 'stock', 'quantity', 'coupon_missing'])
def test_create_order_validates_server_data(context, case):
    c = context
    if case == 'client_missing': c.clients.get_by_id.return_value = None
    if case == 'client_inactive': c.clients.get_by_id.return_value.ativo = False
    if case == 'product_missing': c.products.get_by_id.return_value = None
    if case == 'product_inactive': c.product.ativo = False
    if case == 'stock': c.product.estoque = 0
    c.coupons.get_by_id.return_value = None if case == 'coupon_missing' else Mock()
    if case != 'coupon_missing': c.coupons.get_by_id.return_value.calcular_desconto.return_value = (Decimal('2'), Decimal('18'))
    c.orders.create.side_effect = lambda order: order
    use_case = CreateOrderUseCase(c.clients, c.orders, Mock(), c.coupons, c.products)
    args = (1, 1, [{'product_id': 1, 'quantidade': 0 if case == 'quantity' else 2, 'preco_unitario': 1}], 1)
    if case == 'valid':
        result = use_case.execute(*args)
        assert result.valor_total == Decimal('18')
        assert result.itens[0].preco_unitario == Decimal('10')
    else:
        with pytest.raises(ValueError): use_case.execute(*args)
        c.orders.create.assert_not_called()


@pytest.mark.parametrize('case', ['valid', 'missing', 'inactive', 'order_missing', 'rollback', 'updated_missing'])
def test_confirm_order(context, monkeypatch, case):
    c = context
    monkeypatch.setattr('src.use_cases.order.confirm_order.OrderStatusHistoryRepository', lambda db: c.history)
    if case == 'missing': c.clients.get_by_id.return_value = None
    if case == 'inactive': c.clients.get_by_id.return_value.ativo = False
    if case == 'order_missing': c.orders.get_by_id.return_value = None
    if case == 'rollback': c.history.create.side_effect = RuntimeError('database')
    if case == 'updated_missing': c.orders.get_by_id.side_effect = [c.order, None]
    use_case = ConfirmOrderUseCase(c.clients, c.orders, Mock())
    if case == 'valid':
        assert use_case.execute(1).status == OrderStatus.PAID
        c.orders.db.commit.assert_called_once()
    else:
        with pytest.raises(RuntimeError if case == 'rollback' else ValueError): use_case.execute(1)
        if case == 'rollback': c.orders.db.rollback.assert_called_once()


@pytest.mark.parametrize('case', ['missing', 'updated_missing', 'rollback', 'stale', 'already_canceled'])
def test_cancel_order_edge_cases(context, case):
    c = context
    if case == 'missing': c.orders.get_by_id_for_update.return_value = None
    if case == 'updated_missing': c.orders.get_by_id.return_value = None
    if case == 'rollback': c.history.create.side_effect = RuntimeError('database')
    if case == 'already_canceled': c.order.status = OrderStatus.CANCELED
    use_case = CancelOrderUseCase(c.orders, c.history, c.products)
    if case in ('stale', 'already_canceled'):
        assert use_case.execute(1, expired_before=datetime(2025, 1, 1)) is c.order
        c.products.release_stock.assert_not_called()
    else:
        with pytest.raises(RuntimeError if case == 'rollback' else ValueError): use_case.execute(1)
        if case == 'rollback': c.orders.db.rollback.assert_called_once()


@pytest.mark.parametrize('cls,args', [(CalculateOrderTotalUseCase, (1,)), (UpdateAdminOrderNotesUseCase, (1, 'note'))])
@pytest.mark.parametrize('case', ['valid', 'missing', 'updated_missing'])
def test_order_update_missing_results(context, cls, args, case):
    c = context
    if case == 'missing': c.orders.get_by_id.return_value = None
    if case == 'updated_missing':
        c.orders.update.return_value = None
        c.orders.update_admin_notes.return_value = None
    if case == 'valid': assert cls(c.orders).execute(*args) is not None
    else:
        with pytest.raises(ValueError): cls(c.orders).execute(*args)


@pytest.mark.parametrize('case', ['valid', 'missing', 'status', 'coupon_missing', 'updated_missing'])
def test_apply_coupon(context, case):
    c = context
    if case == 'missing': c.orders.get_by_id.return_value = None
    if case == 'status': c.order.status = OrderStatus.SHIPPED
    if case == 'coupon_missing': c.coupons.get_by_id.return_value = None
    else: c.coupons.get_by_id.return_value.calcular_desconto.return_value = (Decimal('5'), Decimal('15'))
    if case == 'updated_missing': c.orders.update.return_value = None
    if case == 'valid':
        ApplyCouponToOrderUseCase(c.orders, c.coupons).execute(1, 1)
        assert c.orders.update.call_args.args[1]['valor_total'] == Decimal('15')
    else:
        with pytest.raises(ValueError): ApplyCouponToOrderUseCase(c.orders, c.coupons).execute(1, 1)


@pytest.mark.parametrize('case', ['valid', 'missing', 'paid_last_item', 'remove_missing', 'update_missing'])
def test_remove_order_item(context, case):
    c = context
    if case == 'missing': c.orders.get_by_id.return_value = None
    if case == 'paid_last_item': c.order.status = OrderStatus.PAID
    if case == 'remove_missing': c.orders.remove_item.return_value = None
    if case == 'update_missing': c.orders.update.return_value = None
    if case == 'valid':
        assert RemoveOrderItemUseCase(c.orders).execute(1, 1).valor_total == 0
    else:
        with pytest.raises(ValueError): RemoveOrderItemUseCase(c.orders).execute(1, 1)


@pytest.mark.parametrize('identifier,valid', [('BUYER@example.com', True), ('123.456.789-00', True), ('11999998888', True), ('8888', True), ('', False), ('other', False)])
def test_tracking_identifiers(context, identifier, valid):
    c = context
    c.order.customer_email, c.order.customer_cpf, c.order.customer_phone = 'buyer@example.com', '12345678900', '11999998888'
    if valid: assert TrackOrderUseCase(c.orders).execute(1, identifier) is c.order
    else:
        with pytest.raises(ValueError): TrackOrderUseCase(c.orders).execute(1, identifier)
    c.order.ativo = False
    with pytest.raises(ValueError): TrackOrderUseCase(c.orders).execute(1, identifier)


@pytest.mark.parametrize('operation,case', [
    (operation, case)
    for operation in ['create', 'update', 'remove']
    for case in ['valid', 'missing', 'inactive', 'order_missing', 'status', 'quantity', 'stock', 'repository_none']
    if not (operation == 'create' and case in ('missing', 'inactive', 'repository_none'))
    and not (operation == 'remove' and case in ('quantity', 'stock'))
])
def test_order_item_rules(context, operation, case):
    c = context
    if case == 'missing': c.items.get_by_id.return_value = None
    if case == 'inactive': c.order.itens[0].ativo = False
    if case == 'order_missing': c.orders.get_by_id.return_value = None
    if case == 'status': c.order.status = OrderStatus.PAID
    if case == 'stock': c.product.estoque = 0
    if case == 'repository_none':
        c.items.update_quantity.return_value = None
        c.items.deactivate.return_value = None
    quantity = 0 if case == 'quantity' else 2
    if operation == 'create': use_case, args = CreateOrderItemUseCase(c.orders, c.items, c.products), (1, 1, quantity)
    elif operation == 'update': use_case, args = UpdateOrderItemQuantityUseCase(c.orders, c.items, c.products), (1, quantity)
    else: use_case, args = DeactivateItem(c.orders, c.items), (1,)
    if case == 'valid': assert use_case.execute(*args) is not None
    else:
        with pytest.raises(ValueError): use_case.execute(*args)


@pytest.mark.parametrize('cls,method', [(IncreaseProductStockUseCase, 'increase_stock'), (DecreaseProductStockUseCase, 'decrease_stock'), (UpdateProductStockUseCase, 'update_stock')])
@pytest.mark.parametrize('case', ['valid', 'missing', 'invalid', 'repository_none'])
def test_stock_mutations(context, cls, method, case):
    c = context
    if case == 'missing': c.products.get_by_id.return_value = None
    if case == 'repository_none': getattr(c.products, method).return_value = None
    if case == 'valid': assert cls(c.products).execute(1, 2) is getattr(c.products, method).return_value
    else:
        with pytest.raises(ValueError): cls(c.products).execute(1, -1 if case == 'invalid' else 2)


def test_stock_availability_boundaries(context):
    c = context
    assert CheckProductAvailabilityUseCase(c.products).execute(1, 5).disponivel
    assert not CheckProductAvailabilityUseCase(c.products).execute(1, 6).disponivel
    with pytest.raises(ValueError): DecreaseProductStockUseCase(c.products).execute(1, 6)
    c.product.ativo = False
    with pytest.raises(ValueError): CheckProductAvailabilityUseCase(c.products).execute(1, 1)
    c.products.get_by_id.return_value = None
    with pytest.raises(ValueError): CheckProductAvailabilityUseCase(c.products).execute(1, 1)
