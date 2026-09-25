import base64
import json
from email.message import EmailMessage
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

from src.config.config import get_settings
from src.repositories.notification_repository import NotificationRepository


class NotificationConfigurationError(RuntimeError):
    pass


class NotificationDispatcher:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository
        self.settings = get_settings()

    def _send_email(self, notification) -> None:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request as GoogleRequest
        from googleapiclient.discovery import build
        from google_auth_httplib2 import AuthorizedHttp
        from httplib2 import Http

        scopes = ["https://www.googleapis.com/auth/gmail.send"]
        token_path = Path(self.settings.GMAIL_TOKEN_FILE or "gmail-token.json")
        if not self.settings.GMAIL_SENDER or not token_path.is_file():
            raise NotificationConfigurationError("Configure GMAIL_SENDER e um token Gmail autorizado antes do envio")
        credentials = Credentials.from_authorized_user_file(token_path, scopes) if token_path.exists() else None
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
        if not credentials or not credentials.valid:
            raise NotificationConfigurationError("Token Gmail inválido; execute python -m src.authorize_gmail fora do worker")
        message = EmailMessage()
        message["To"] = notification.recipient
        message["From"] = self.settings.GMAIL_SENDER
        message["Subject"] = notification.subject or "GG Imports"
        message.set_content(notification.body)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        http = AuthorizedHttp(credentials, http=Http(timeout=20))
        build("gmail", "v1", http=http).users().messages().send(userId="me", body={"raw": raw}).execute()

    def _send_whatsapp(self, notification) -> None:
        if not self.settings.WHATSAPP_ACCESS_TOKEN or not self.settings.WHATSAPP_PHONE_NUMBER_ID:
            raise NotificationConfigurationError("Credenciais do WhatsApp não configuradas")
        url = f"https://graph.facebook.com/{self.settings.WHATSAPP_API_VERSION}/{self.settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        payload = json.dumps({"messaging_product": "whatsapp", "to": notification.recipient, "type": "text", "text": {"body": notification.body}}).encode()
        request = Request(url, data=payload, headers={"Authorization": f"Bearer {self.settings.WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=20):
            pass

    def dispatch_pending(self, limit: int = 100, *, should_stop: Callable[[], bool] | None = None) -> dict:
        sent = failed = deferred = 0
        for notification in self.repository.list_pending(limit):
            if should_stop and should_stop():
                break
            try:
                if notification.channel == "EMAIL":
                    self._send_email(notification)
                elif notification.channel == "WHATSAPP":
                    self._send_whatsapp(notification)
                else:
                    raise RuntimeError("Canal de notificação desconhecido")
                self.repository.mark_sent(notification.id)
                sent += 1
            except NotificationConfigurationError:
                # Missing configuration must not exhaust delivery attempts before setup.
                deferred += 1
            except Exception as exc:
                self.repository.mark_failed(notification.id, str(exc))
                failed += 1
        return {"sent": sent, "failed": failed, "deferred": deferred}
