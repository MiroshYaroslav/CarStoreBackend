import uuid

import boto3
from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import settings


class S3Service:
    def __init__(self):
        if not settings.AWS_BUCKET_NAME or not settings.AWS_REGION:
            raise RuntimeError("AWS_BUCKET_NAME and AWS_REGION must be configured to upload images")
        self.s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
        self.bucket_name = settings.AWS_BUCKET_NAME

    async def upload_image(self, file: UploadFile) -> str:
        file_extension = (file.filename or "").rsplit(".", 1)[-1].lower()
        if not file_extension.isalnum() or len(file_extension) > 10:
            file_extension = "bin"
        unique_filename = f"products/{uuid.uuid4()}.{file_extension}"

        await run_in_threadpool(
            self.s3_client.upload_fileobj,
            file.file,
            self.bucket_name,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )

        return (
            f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"
        )
