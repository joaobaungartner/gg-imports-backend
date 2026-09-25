"""One-time interactive Gmail authorization on the operator's workstation."""

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from src.config.config import get_settings


def main():
    settings = get_settings()
    if not settings.GMAIL_CREDENTIALS_FILE:
        raise ValueError("Configure GMAIL_CREDENTIALS_FILE no .env")
    flow = InstalledAppFlow.from_client_secrets_file(
        settings.GMAIL_CREDENTIALS_FILE, ["https://www.googleapis.com/auth/gmail.send"]
    )
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    token_path = Path(settings.GMAIL_TOKEN_FILE or "gmail-token.json")
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    print("Autorização salva. O worker já pode usar o token sem abrir navegador.")


if __name__ == "__main__":
    main()
