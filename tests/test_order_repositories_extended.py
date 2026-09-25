from datetime import datetime, date
from decimal import Decimal

import pytest

from src.entities.order import OrderEntity
from src.entities.order_item import OrderItemEntity
from src.models import PaymentModel, UserModel
from src.repositories.order_repository import OrderRepository
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_status_history_repository import OrderStatusHistoryRepository


@pytest.fixture
def orders(db_session):
    repo = OrderRepository(db_session)
    for id_, status, shipping, when in [(1, 'PENDING_PAYMENT', 'ENTREGA', 1), (2, 'PAID', 'RETIRADA', 2), (3, 'SHIPPED', 'ENTREGA', 3)]:
        from src.entities.order import OrderStatus
        repo.create(OrderEntity(id_, client_id=1, endereco_id=1, customer_name='Buyer',
            customer_email='buyer@example.com', status=OrderStatus(status), shipping_method=shipping,
            payment_method='PIX', data_pedido=datetime(2025, 1, when),
            itens=[OrderItemEntity(1, 2, 10, id=id_)]))
    db_session.add(PaymentModel(order_id=2, metodo='PIX', valor=20, status='PAID'))
    db_session.commit()
    return repo


def test_order_queries(orders):
    assert [o.id for o in orders.list_all()] == [3, 2, 1]
    assert [o.id for o in orders.get_by_client_id(1)] == [3, 2, 1]
    assert [o.id for o in orders.list_by_status('PAID')] == [2]
    assert orders.get_by_client_id(999) == []
    assert orders.get_payment_status(1) is None
    assert orders.get_payment_status(2) == 'PAID'
    assert orders.get_by_id(999) is None
    assert orders.get_by_id_for_update(999) is None


@pytest.mark.parametrize('filters,ids', [
    ({'status': 'PAID', 'shipping_method': 'retirada', 'payment_method': 'pix', 'payment_status': 'paid'}, [2]),
    ({'payment_status': 'PENDING_PAYMENT'}, [3, 1]),
    ({'date_from': date(2025, 1, 2), 'date_to': date(2025, 1, 2)}, [2]),
    ({'search': 'buyer', 'sort': 'asc'}, [1, 2, 3]),
    ({'search': '2'}, [2]), ({'search': 'absent'}, []),
    ({'page': 2, 'page_size': 1}, [2]),
])
def test_admin_filters(orders, filters, ids):
    result = orders.list_admin_paginated(**filters)
    assert [item['order'].id for item in result['items']] == ids
    assert result['total'] == (3 if 'page' in filters else len(ids))


def test_summary_and_pagination_bounds(orders):
    assert orders.admin_summary(date_from=date(2025, 1, 1), date_to=date(2025, 1, 3)) == dict(
        total=3, pending_payment=1, preparing=1, shipped_or_ready=1, delivered=0, canceled=0)
    result = orders.list_admin_paginated(page=0, page_size=1000)
    assert (result['page'], result['page_size'], result['total_pages']) == (1, 100, 1)


def test_order_mutations(orders):
    assert orders.update(999, {}) is None
    assert orders.update_status(999, 'PAID') is None
    assert orders.update_status(1, 'PAID').status.value == 'PAID'
    assert orders.update_admin_notes(1, 'Call customer').admin_notes == 'Call customer'
    assert not orders.deactivate(1).ativo
    assert orders.add_item(999, OrderItemEntity(1, 1, 10)) is None
    added = orders.add_item(1, OrderItemEntity(1, 3, 10))
    assert len(added.itens) == 2
    assert orders.remove_item(999, 1) is None
    assert orders.remove_item(1, 999) is None
    assert len(orders.remove_item(1, added.itens[-1].id).itens) == 1
    assert orders.delete(1)
    assert not orders.delete(999)


def test_order_item_repository(db_session):
    repo = OrderItemRepository(db_session)
    with pytest.raises(ValueError): repo.create(OrderItemEntity(1, 1, 10))
    item = repo.create(OrderItemEntity(1, 2, 10, id=1, order_id=1))
    assert repo.get_by_id(1) == item
    assert repo.get_by_id(999) is None
    assert repo.get_by_order_id(1) == [item]
    assert repo.get_by_product_id(1) == [item]
    assert repo.get_by_order_and_product(1, 1) == item
    assert repo.list_all() == [item]
    assert repo.update_quantity(1, 3).quantidade == 3
    assert not repo.deactivate(1).ativo
    assert repo.get_by_order_and_product(1, 1) is None
    assert repo.update(999, {}) is None
    assert repo.delete(1)
    assert not repo.delete(1)
    repo.create(OrderItemEntity(1, 1, 10, order_id=2))
    assert repo.delete_by_order_id(2) == 1
    assert repo.delete_by_order_id(2) == 0


def test_order_history_records_actor(db_session, orders):
    db_session.add(UserModel(id=1, nome='Admin', email='admin@example.com', senha_hash='test', role='ADMIN'))
    db_session.commit()
    repo = OrderStatusHistoryRepository(db_session)
    event = repo.create(1, 'PAID', 'PREPARING', changed_by_user_id=1, note='Packed', commit=True)
    assert event.changed_by_name == 'Admin'
    assert repo.list_by_order_id(1)[0].note == 'Packed'
    assert repo.list_by_order_id(999) == []
