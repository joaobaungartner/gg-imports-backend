from src.database.database import SessionLocal
from src.repositories.notification_repository import NotificationRepository
from src.services.notification_dispatcher import NotificationDispatcher


if __name__ == "__main__":
    db = SessionLocal()
    try:
        print(NotificationDispatcher(NotificationRepository(db)).dispatch_pending())
    finally:
        db.close()
