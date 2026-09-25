from datetime import datetime, timedelta
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src import background_worker as worker
from src.database.database import Base
from src.models.notification_model import NotificationModel
from src.models.order_model import OrderModel
from src.repositories.notification_repository import NotificationRepository
from src.services.notification_dispatcher import NotificationDispatcher, NotificationConfigurationError


@pytest.fixture
def database(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{(tmp_path / 'worker.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(worker, "SessionLocal", sessions)
    with sessions() as db:
        NotificationRepository(db).enqueue(channel="EMAIL", event="PASSWORD_RESET",
                                           recipient="customer@example.com", body="Reset link")
        db.add(OrderModel(
            id=1, customer_name="Cliente", customer_email="customer@example.com",
            shipping_cep="01001000", shipping_street="Rua", shipping_number="1",
            shipping_neighborhood="Centro", shipping_city="SP", shipping_state="SP",
            status="PENDING_PAYMENT", estoque_reservado=True,
            reserva_expira_em=datetime.utcnow() - timedelta(minutes=1), valor_total=100,
        ))
        db.commit()
    yield sessions
    engine.dispose()


def test_jobs_deliver_pending_mail_and_expire_without_checkout(database, monkeypatch):
    delivered = []
    monkeypatch.setattr(NotificationDispatcher, "_send_email", lambda self, n: delivered.append(n.id))
    worker.dispatch_notifications(Event())
    worker.expire_reservations(Event())
    worker.dispatch_notifications(Event())
    worker.expire_reservations(Event())
    with database() as db:
        assert db.query(NotificationModel).one().status == "SENT"
        assert db.query(NotificationModel).one().attempts == 1
        order = db.get(OrderModel, 1)
        assert order.status == "CANCELED"
        assert not order.estoque_reservado
    assert len(delivered) == 1


def test_unconfigured_channel_does_not_consume_retries(database, monkeypatch):
    monkeypatch.setattr("src.services.notification_dispatcher.get_settings", lambda: SimpleNamespace(
        GMAIL_SENDER=None, GMAIL_TOKEN_FILE=None))
    for _ in range(6):
        worker.dispatch_notifications(Event())
    with database() as db:
        notification = db.query(NotificationModel).one()
        assert notification.status == "PENDING"
        assert notification.attempts == 0


def test_failed_delivery_retries_on_next_cycle(database, monkeypatch):
    send = Mock(side_effect=[RuntimeError("provider unavailable"), None])
    monkeypatch.setattr(NotificationDispatcher, "_send_email", send)
    worker.dispatch_notifications(Event())
    with database() as db:
        assert db.query(NotificationModel).one().status == "FAILED"
    worker.dispatch_notifications(Event())
    with database() as db:
        notification = db.query(NotificationModel).one()
        assert notification.status == "SENT"
        assert notification.attempts == 2


def test_shutdown_stops_dispatch_before_next_message(database, monkeypatch):
    send = Mock()
    monkeypatch.setattr(NotificationDispatcher, "_send_email", send)
    stopped = Event()
    stopped.set()
    worker.dispatch_notifications(stopped)
    send.assert_not_called()
    with database() as db:
        assert db.query(NotificationModel).one().status == "PENDING"


def test_periodic_job_recovers_from_exception_without_busy_loop():
    stop = Mock()
    stop.is_set.return_value = False
    stop.wait.side_effect = [False, True]
    job = Mock(side_effect=[RuntimeError("database unavailable"), None])
    worker.run_periodically("test", job, 30, stop)
    assert job.call_count == 2
    assert stop.wait.call_args_list == [((30,),), ((30,),)]


def test_once_attempts_both_jobs_even_if_notifications_fail(monkeypatch):
    monkeypatch.setattr("sys.argv", ["worker", "--once"])
    monkeypatch.setattr(worker, "configure_logging", lambda: None)
    monkeypatch.setattr(worker.signal, "signal", lambda *args: None)
    dispatch = Mock(side_effect=RuntimeError("database unavailable"))
    expire = Mock()
    monkeypatch.setattr(worker, "dispatch_notifications", dispatch)
    monkeypatch.setattr(worker, "expire_reservations", expire)
    assert worker.main() == 1
    expire.assert_called_once()


def test_invalid_gmail_token_never_starts_interactive_authorization(tmp_path, monkeypatch):
    token = tmp_path / "token.json"
    token.write_text("{}")
    monkeypatch.setattr("src.services.notification_dispatcher.get_settings", lambda: SimpleNamespace(
        GMAIL_SENDER="shop@example.com", GMAIL_TOKEN_FILE=str(token)))
    monkeypatch.setattr("google.oauth2.credentials.Credentials.from_authorized_user_file",
                        lambda *args: SimpleNamespace(expired=False, valid=False))
    with pytest.raises(NotificationConfigurationError):
        NotificationDispatcher(Mock())._send_email(SimpleNamespace())
