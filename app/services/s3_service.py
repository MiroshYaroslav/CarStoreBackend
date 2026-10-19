import uuid

import boto3
from fastapi import HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.config import settings


class S3Service:
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    IMAGE_TYPES = {
        "image/jpeg": ("jpg", lambda header: header.startswith(b"\xff\xd8\xff")),
        "image/png": ("png", lambda header: header.startswith(b"\x89PNG\r\n\x1a\n")),
        "image/webp": (
            "webp",
            lambda header: len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP",
        ),
    }

    def __init__(self):
        if not all(
            [
                settings.AWS_BUCKET_NAME,
                settings.AWS_REGION,
                settings.AWS_CLOUDFRONT_DOMAIN,
            ]
        ):
            raise RuntimeError(
                "AWS_BUCKET_NAME, AWS_REGION, and AWS_CLOUDFRONT_DOMAIN "
                "must be configured to upload images"
            )
        self.s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
        self.bucket_name = settings.AWS_BUCKET_NAME

    async def upload_image(self, file: UploadFile) -> str:
        file_type = self.IMAGE_TYPES.get(file.content_type or "")
        if file_type is None:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Only JPEG, PNG, and WebP images are supported",
            )

        if file.size is None or file.size == 0:
            raise HTTPException(status_code=400, detail="The image file is empty")
        if file.size > self.MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail="Image must not exceed 5 MiB")

        file_extension, is_valid_image = file_type
        header = await file.read(12)
        await file.seek(0)
        if not is_valid_image(header):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="The file content does not match its image type",
            )

        unique_filename = f"products/{uuid.uuid4()}.{file_extension}"

        await run_in_threadpool(
            self.s3_client.upload_fileobj,
            file.file,
            self.bucket_name,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )

        return f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{unique_filename}"
