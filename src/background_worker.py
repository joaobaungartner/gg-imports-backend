"""Periodic jobs, independent of API traffic. Run one worker per deployment."""

import argparse
import logging
import signal
from threading import Event, Thread

from src.config.config import get_settings
from src.database.database import SessionLocal
from src.middlewares.production import configure_logging
from src.repositories.notification_repository import NotificationRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.order_status_history_repository import OrderStatusHistoryRepository
from src.repositories.product_repository import ProductRepository
from src.services.notification_dispatcher import NotificationDispatcher
from src.use_cases.order.expire_stock_reservations import ExpireStockReservationsUseCase

logger = logging.getLogger("gg_imports.worker")


def dispatch_notifications(stop_event: Event):
    with SessionLocal() as db:
        result = NotificationDispatcher(NotificationRepository(db)).dispatch_pending(
            limit=get_settings().NOTIFICATION_BATCH_SIZE,
            should_stop=stop_event.is_set,
        )
        logger.info("notifications result=%s", result)


def expire_reservations(stop_event: Event):
    with SessionLocal() as db:
        expired = ExpireStockReservationsUseCase(
            OrderRepository(db), ProductRepository(db), OrderStatusHistoryRepository(db)
        ).execute()
        logger.info("reservations expired_count=%s", len(expired))


def run_periodically(name, job, interval: int, stop_event: Event):
    # Jobs run immediately, then wait after completion: no overlapping cycles.
    while not stop_event.is_set():
        try:
            job(stop_event)
        except Exception:
            logger.exception("job_failed job=%s; retrying_next_cycle", name)
        if stop_event.wait(interval):
            break


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Run both jobs once and exit")
    args = parser.parse_args()
    configure_logging()
    settings = get_settings()
    stop_event = Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop_event.set())
    jobs = [
        ("notifications", dispatch_notifications, settings.NOTIFICATION_INTERVAL_SECONDS),
        ("reservations", expire_reservations, settings.RESERVATION_EXPIRATION_INTERVAL_SECONDS),
    ]
    if args.once:
        failed = False
        for name, job, _ in jobs:
            try:
                job(stop_event)
            except Exception:
                logger.exception("job_failed job=%s", name)
                failed = True
        return int(failed)

    # Separate sessions and threads keep slow email providers from blocking stock release.
    threads = [Thread(target=run_periodically, args=(*job, stop_event), name=job[0]) for job in jobs]
    for thread in threads:
        thread.start()
    logger.info("worker_started")
    try:
        stop_event.wait()
    finally:
        stop_event.set()
        for thread in threads:
            thread.join()
        logger.info("worker_stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
