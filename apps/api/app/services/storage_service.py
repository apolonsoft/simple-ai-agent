# app/services/storage_service.py
import asyncio
import io
import uuid
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.core.config import settings


class StorageService:
    def __init__(self, s3_client: Any | None = None) -> None:
        self.bucket_name = settings.S3_BUCKET_NAME
        self.public_url_prefix = settings.S3_PUBLIC_URL_PREFIX.rstrip("/")
        self.client = s3_client or boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self._bucket_verified = False

    def _ensure_bucket(self) -> None:
        if self._bucket_verified:
            return
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            self._bucket_verified = True
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket_name)
                self._bucket_verified = True
            except ClientError:
                # If bucket already exists or cannot be created, keep proceeding
                pass

    def _sync_upload(self, file_bytes: bytes, key: str, content_type: str) -> None:
        self._ensure_bucket()
        self.client.upload_fileobj(
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
        extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "bin"
        unique_key = f"{uuid.uuid4().hex}.{extension}"

        try:
            await asyncio.to_thread(self._sync_upload, file_bytes, unique_key, content_type)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage upload failed: {str(e)}",
            ) from e

        return f"{self.public_url_prefix}/{unique_key}"
