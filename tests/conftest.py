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
