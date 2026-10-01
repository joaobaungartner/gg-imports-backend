from src.models.product_model import ProductModel
from types import SimpleNamespace
import pytest


def test_deactivation_can_be_reversed_but_deletion_disappears(commerce_api, db_session):
    client = commerce_api
    assert client.patch('/products/1/deactivate').status_code == 200
    assert any(p['id'] == 1 for p in client.get('/products/?active=false').json())
    assert client.patch('/products/activate-many', json={'product_ids': [1]}).status_code == 200
    assert any(p['id'] == 1 for p in client.get('/products/?active=true').json())
    response = client.request('DELETE', '/products/delete-many', json={'product_ids': [1]})
    assert response.status_code == 200, response.text
    for path in ('/products/', '/products/?active=false', '/products/?active=true', '/products/search?q=Shirt&apenas_ativos=false'):
        assert not any(p['id'] == 1 for p in client.get(path).json())
    assert client.get('/products/1').status_code >= 400
    assert client.patch('/products/1/activate').status_code >= 400
    row = db_session.get(ProductModel, 1)
    assert row.excluido and not row.ativo


def test_bulk_delete_rolls_back_if_a_variant_is_missing(commerce_api, db_session):
    response = commerce_api.request('DELETE', '/products/delete-many', json={'product_ids': [1, 9999]})
    assert response.status_code >= 400
    db_session.expire_all()
    assert not db_session.get(ProductModel, 1).excluido


def test_linked_order_prevents_deletion_even_if_item_is_inactive(commerce_api, db_session):
    from src.repositories.product_repository import ProductRepository
    from src.use_cases.product.delete_product import DeleteProductUseCase
    orders = SimpleNamespace(get_by_product_id=lambda _: [SimpleNamespace(ativo=False)])
    use_case = DeleteProductUseCase(ProductRepository(db_session), orders)
    with pytest.raises(ValueError, match="pedidos vinculados"):
        use_case.execute(1)
    assert not db_session.get(ProductModel, 1).excluido


def test_migration_keeps_existing_inactive_products_reactivatable():
    import importlib.util
    from pathlib import Path
    from sqlalchemy import create_engine, text
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    path = Path(__file__).parents[1] / 'alembic/versions/c82d6a9e410f_separate_product_deletion.py'
    spec = importlib.util.spec_from_file_location('product_deletion_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE products (id INTEGER PRIMARY KEY, ativo BOOLEAN NOT NULL)'))
        connection.execute(text('INSERT INTO products VALUES (1, 0)'))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert connection.execute(text('SELECT excluido FROM products WHERE id=1')).scalar() == 0
    engine.dispose()
