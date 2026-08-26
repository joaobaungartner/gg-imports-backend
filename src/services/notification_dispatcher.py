import base64
import json
from email.message import EmailMessage
from pathlib import Path
from urllib.request import Request, urlopen

from src.config.config import get_settings
from src.repositories.notification_repository import NotificationRepository


class NotificationDispatcher:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository
        self.settings = get_settings()

    def _send_email(self, notification) -> None:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request as GoogleRequest
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        scopes = ["https://www.googleapis.com/auth/gmail.send"]
        token_path = Path(self.settings.GMAIL_TOKEN_FILE or "gmail-token.json")
        credentials = Credentials.from_authorized_user_file(token_path, scopes) if token_path.exists() else None
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
        if not credentials or not credentials.valid:
            if not self.settings.GMAIL_CREDENTIALS_FILE:
                raise RuntimeError("GMAIL_CREDENTIALS_FILE não configurado")
            flow = InstalledAppFlow.from_client_secrets_file(self.settings.GMAIL_CREDENTIALS_FILE, scopes)
            credentials = flow.run_local_server(port=0)
            token_path.write_text(credentials.to_json(), encoding="utf-8")
        message = EmailMessage()
        message["To"] = notification.recipient
        message["From"] = self.settings.GMAIL_SENDER
        message["Subject"] = notification.subject or "GG Imports"
        message.set_content(notification.body)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        build("gmail", "v1", credentials=credentials).users().messages().send(userId="me", body={"raw": raw}).execute()

    def _send_whatsapp(self, notification) -> None:
        if not self.settings.WHATSAPP_ACCESS_TOKEN or not self.settings.WHATSAPP_PHONE_NUMBER_ID:
            raise RuntimeError("Credenciais do WhatsApp não configuradas")
        url = f"https://graph.facebook.com/{self.settings.WHATSAPP_API_VERSION}/{self.settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        payload = json.dumps({"messaging_product": "whatsapp", "to": notification.recipient, "type": "text", "text": {"body": notification.body}}).encode()
        request = Request(url, data=payload, headers={"Authorization": f"Bearer {self.settings.WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=20):
            pass

    def dispatch_pending(self, limit: int = 100) -> dict:
        sent = failed = 0
        for notification in self.repository.list_pending(limit):
            try:
                if notification.channel == "EMAIL":
                    self._send_email(notification)
                elif notification.channel == "WHATSAPP":
                    self._send_whatsapp(notification)
                else:
                    raise RuntimeError("Canal de notificação desconhecido")
                self.repository.mark_sent(notification.id)
                sent += 1
            except Exception as exc:
                self.repository.mark_failed(notification.id, str(exc))
                failed += 1
        return {"sent": sent, "failed": failed}
