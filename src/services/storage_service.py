import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile

from src.config.config import get_settings

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

S3_ENV_VARS = (
    "S3_BUCKET_NAME",
    "S3_ENDPOINT_URL",
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "S3_REGION",
    "S3_PUBLIC_BASE_URL",
)


class StorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket_name = settings.S3_BUCKET_NAME
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.access_key_id = settings.S3_ACCESS_KEY_ID
        self.secret_access_key = settings.S3_SECRET_ACCESS_KEY
        self.region = settings.S3_REGION
        self.public_base_url = (settings.S3_PUBLIC_BASE_URL or "").rstrip("/")

    def _validate_config(self) -> None:
        values = {
            "S3_BUCKET_NAME": self.bucket_name,
            "S3_ENDPOINT_URL": self.endpoint_url,
            "S3_ACCESS_KEY_ID": self.access_key_id,
            "S3_SECRET_ACCESS_KEY": self.secret_access_key,
            "S3_REGION": self.region,
            "S3_PUBLIC_BASE_URL": self.public_base_url,
        }
        missing = [
            name
            for name in S3_ENV_VARS
            if not values[name] or not str(values[name]).strip()
        ]
        if missing:
            raise ValueError(
                f"Configuração S3 incompleta. Variáveis ausentes: {', '.join(missing)}"
            )

    def _get_client(self):
        self._validate_config()
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
        )

    async def upload_product_image(self, file: UploadFile) -> str:
        content_type = (file.content_type or "").lower()
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("Formato de imagem inválido. Use JPG, PNG ou WEBP.")

        content = await file.read()
        if not content:
            raise ValueError("Arquivo de imagem vazio.")
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise ValueError("A imagem deve ter no máximo 5MB.")

        extension = ALLOWED_CONTENT_TYPES[content_type]
        object_key = f"products/{uuid.uuid4()}.{extension}"

        try:
            client = self._get_client()
            client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=content,
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as error:
            raise ValueError("Falha ao enviar imagem para o armazenamento.") from error

        return f"{self.public_base_url}/{object_key}"
