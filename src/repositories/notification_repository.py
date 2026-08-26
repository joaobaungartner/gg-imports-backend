from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.models.notification_model import NotificationModel


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def enqueue(
        self,
        *,
        channel: str,
        event: str,
        recipient: str,
        body: str,
        subject: str | None = None,
        commit: bool = True,
    ) -> NotificationModel:
        model = NotificationModel(
            channel=channel,
            event=event,
            recipient=recipient,
            subject=subject,
            body=body,
            status="PENDING",
            created_at=datetime.utcnow(),
        )
        self.db.add(model)
        if commit:
            self.db.commit()
            self.db.refresh(model)
        else:
            self.db.flush()
        return model

    def list_pending(self, limit: int = 100) -> list[NotificationModel]:
        return (
            self.db.query(NotificationModel)
            .filter(or_(
                NotificationModel.status == "PENDING",
                (NotificationModel.status == "FAILED") & (NotificationModel.attempts < 5),
            ))
            .order_by(NotificationModel.created_at.asc())
            .limit(limit)
            .all()
        )

    def mark_sent(self, notification_id: int) -> None:
        model = self.db.query(NotificationModel).filter_by(id=notification_id).first()
        if model:
            model.status = "SENT"
            model.sent_at = datetime.utcnow()
            model.attempts += 1
            self.db.commit()

    def mark_failed(self, notification_id: int, error: str) -> None:
        model = self.db.query(NotificationModel).filter_by(id=notification_id).first()
        if model:
            model.status = "FAILED"
            model.last_error = error[:2000]
            model.attempts += 1
            self.db.commit()
