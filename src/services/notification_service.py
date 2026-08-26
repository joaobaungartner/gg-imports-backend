from src.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    def email(self, event: str, recipient: str, subject: str, body: str, *, commit=True):
        return self.repository.enqueue(
            channel="EMAIL", event=event, recipient=recipient,
            subject=subject, body=body, commit=commit,
        )

    def whatsapp(self, event: str, recipient: str, body: str, *, commit=True):
        return self.repository.enqueue(
            channel="WHATSAPP", event=event, recipient=recipient,
            body=body, commit=commit,
        )
