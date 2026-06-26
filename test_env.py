import os
from dotenv import load_dotenv

load_dotenv()

print("S3_BUCKET_NAME:", os.getenv("S3_BUCKET_NAME"))
print("S3_ENDPOINT_URL:", os.getenv("S3_ENDPOINT_URL"))
print("S3_ACCESS_KEY_ID:", os.getenv("S3_ACCESS_KEY_ID"))
print("S3_SECRET_ACCESS_KEY existe:", bool(os.getenv("S3_SECRET_ACCESS_KEY")))
print("S3_REGION:", os.getenv("S3_REGION"))
print("S3_PUBLIC_BASE_URL:", os.getenv("S3_PUBLIC_BASE_URL"))