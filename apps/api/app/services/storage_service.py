# app/services/storage_service.py
import asyncio
import io
import threading
import uuid
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.core.config import settings

_s3_client: Any | None = None
_s3_client_lock = threading.Lock()
_bucket_verified = False


def _get_s3_client() -> Any:
    """Return the process-wide lazy S3 client, creating it once under a lock."""
    global _s3_client
    if _s3_client is None:
        with _s3_client_lock:
            if _s3_client is None:
                _s3_client = boto3.client(
                    "s3",
                    endpoint_url=settings.S3_ENDPOINT_URL,
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_KEY,
                    config=Config(signature_version="s3v4"),
                    region_name="us-east-1",
                )
    return _s3_client


class StorageService:
    def __init__(self, s3_client: Any | None = None) -> None:
        self.bucket_name = settings.S3_BUCKET_NAME
        self.public_url_prefix = settings.S3_PUBLIC_URL_PREFIX.rstrip("/")
        self.client = s3_client

    def _ensure_bucket(self, client: Any) -> None:
        global _bucket_verified
        if _bucket_verified:
            return
        try:
            client.head_bucket(Bucket=self.bucket_name)
            _bucket_verified = True
        except ClientError:
            try:
                client.create_bucket(Bucket=self.bucket_name)
                _bucket_verified = True
            except ClientError:
                # If bucket already exists or cannot be created, keep proceeding
                pass

    def _sync_upload(self, file_bytes: bytes, key: str, content_type: str) -> None:
        client = self.client or _get_s3_client()
        self._ensure_bucket(client)
        client.upload_fileobj(
            Fileobj=io.BytesIO(file_bytes),
            Bucket=self.bucket_name,
            Key=key,
            ExtraArgs={"ContentType": content_type},
        )

    async def upload_file(
        self, file_bytes: bytes, original_filename: str, content_type: str
    ) -> str:
        """Uploads a file stream asynchronously to S3/SeaweedFS and returns its public URL."""
        # Sanitize extension and create unique object key
        extension = (
            original_filename.rsplit(".", 1)[-1].lower()
            if "." in original_filename
            else "bin"
        )
        unique_key = f"{uuid.uuid4().hex}.{extension}"

        try:
            await asyncio.to_thread(
                self._sync_upload, file_bytes, unique_key, content_type
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage upload failed: {str(e)}",
            ) from e

        return f"{self.public_url_prefix}/{unique_key}"
