"""Keep the suite independent of the developer's database and credentials."""
import os
import tempfile
from pathlib import Path

import pytest


# Settings are loaded during collection, before fixtures can override get_db.
_database_dir = tempfile.TemporaryDirectory(prefix='gg-imports-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(_database_dir.name) / 'tests.db').as_posix()
os.environ['SECRET_KEY'] = 'test-only-secret-key-not-for-production'
for _name in ('MERCADO_PAGO_ACCESS_TOKEN', 'MERCADO_PAGO_WEBHOOK_SECRET',
              'GMAIL_SENDER', 'WHATSAPP_ACCESS_TOKEN'):
    os.environ[_name] = ''


@pytest.fixture(scope='session', autouse=True)
def isolated_database():
    from sqlalchemy import JSON
    from src.database.database import Base, engine
    from src.models.site_content_model import SiteContentModel

    # These tests exercise JSON persistence, not PostgreSQL JSONB operators.
    column = SiteContentModel.__table__.c.payload
    original = column.type
    column.type = original.with_variant(JSON(), 'sqlite')
    Base.metadata.create_all(engine)
    yield
    engine.dispose()
    column.type = original
    _database_dir.cleanup()


@pytest.fixture
def commerce_api(db_session):
    """Real routes/use cases/repositories; only authentication identity is injected."""
    from datetime import date
    from importlib import import_module
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.database.database import get_db
    from src.middlewares.auth import get_current_user, get_current_admin, get_optional_user
    from src.entities.user import UserEntity, UserRole
    from src.models import UserModel, ClientModel, AddressModel, CategoryModel, ProductModel
    from src.models.coupon_model import CouponModel
    from src.models.product_collection_model import ProductCollectionModel

    db_session.add_all([
        UserModel(id=1, nome='Buyer', email='buyer@example.com', senha_hash='test', role='CLIENTE'),
        ClientModel(id=1, user_id=1, cpf='12345678900'),
        AddressModel(id=1, client_id=1, rua='Rua', numero='1', bairro='Centro', cidade='SP', estado='SP', cep='01001000'),
        CategoryModel(id=1, nome='Shirts'),
        ProductModel(id=1, category_id=1, nome='Shirt', preco=100, tamanho='M', clube='Club', tipo='Fan', estoque=20),
        CouponModel(id=1, codigo='SAVE10', desconto=10, validade=date(2099, 1, 1)),
        ProductCollectionModel(slug='promotions', name='Promotions'),
        ProductCollectionModel(slug='launches', name='Launches'),
    ])
    db_session.commit()
    user = UserEntity(1, 'Buyer', 'buyer@example.com', 'test', role=UserRole.ADMIN)
    app = FastAPI()
    for name in ('order', 'order_item', 'admin_order', 'product', 'category', 'coupon',
                 'address', 'cart', 'cart_item', 'client', 'admin', 'admin_management',
                 'admin_collection', 'post_sale'):
        app.include_router(import_module('src.routes.' + name + '_routes').router)
    from src.routes.site_content_routes import public_router, admin_router
    from src.routes.post_sale_routes import admin_router as post_sale_admin
    for router in (public_router, admin_router, post_sale_admin):
        app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db_session
    for dependency in (get_current_user, get_current_admin, get_optional_user):
        app.dependency_overrides[dependency] = lambda: user
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db_session(isolated_database):
    """A fresh database for each integration test, including its HTTP requests."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool
    from src.database.database import Base

    engine = create_engine('sqlite://', poolclass=StaticPool,
                           connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()
