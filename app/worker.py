import asyncio
import json
import logging
import signal
import uuid

import boto3
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionMaker, engine
from app.models.async_task import AsyncTask, TaskStatus
from app.repositories.callback_request_repository import CallbackRequestRepository
from app.schemas.callback_request import CallbackRequestCreate
from app.services.callback_request_service import CallbackRequestService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bmw_sqs_worker")

sqs_client = boto3.client("sqs", region_name=settings.AWS_REGION or "eu-central-1")


class GracefulShutdown:
    def __init__(self) -> None:
        self.stop = False
        signal.signal(signal.SIGTERM, self._on_signal)
        signal.signal(signal.SIGINT, self._on_signal)

    def _on_signal(self, signum: int, _frame: object) -> None:
        logger.info("Signal %s received, finishing current batch...", signum)
        self.stop = True


async def handle_message(db: AsyncSession, body: dict) -> None:
    task_id = uuid.UUID(body["task_id"])
    payload = CallbackRequestCreate(**body["data"])

    result = await db.execute(
        select(AsyncTask).where(AsyncTask.id == task_id).with_for_update()
    )
    task = result.scalar_one_or_none()
    if not task:
        logger.warning("Task %s not found in DB, skipping.", task_id)
        return

    if task.status == TaskStatus.COMPLETED:
        logger.info("Task %s already completed, skipping duplicate.", task_id)
        return

    task.status = TaskStatus.PROCESSING
    await db.flush()

    try:
        repo = CallbackRequestRepository(db)
        service = CallbackRequestService(db, repo)
        created = await service.create_request(payload)

        task.status = TaskStatus.COMPLETED
        task.result = json.dumps(jsonable_encoder({"callback_request_id": created.id}))
        await db.commit()
        logger.info("Task %s completed -> callback_request %s", task_id, created.id)
    except Exception as exc:
        await db.rollback()
        logger.exception("Task %s failed: %s", task_id, exc)
        async with AsyncSessionMaker() as err_db:
            res = await err_db.execute(select(AsyncTask).where(AsyncTask.id == task_id))
            failed_task = res.scalar_one_or_none()
            if failed_task:
                failed_task.status = TaskStatus.FAILED
                failed_task.error_message = str(exc)
                await err_db.commit()
        raise


async def main() -> None:
    if not settings.SQS_QUEUE_URL:
        raise RuntimeError("SQS_QUEUE_URL is not set")

    shutdown = GracefulShutdown()
    logger.info("Worker listening on %s", settings.SQS_QUEUE_URL)

    try:
        while not shutdown.stop:
            response = await asyncio.to_thread(
                sqs_client.receive_message,
                QueueUrl=settings.SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
            )

            for msg in response.get("Messages", []):
                if shutdown.stop:
                    break

                try:
                    body = json.loads(msg["Body"])
                    async with AsyncSessionMaker() as db:
                        await handle_message(db, body)

                    await asyncio.to_thread(
                        sqs_client.delete_message,
                        QueueUrl=settings.SQS_QUEUE_URL,
                        ReceiptHandle=msg["ReceiptHandle"],
                    )
                except Exception:
                    logger.error("Message %s left in queue for retry", msg.get("MessageId"))
    finally:
        await engine.dispose()
        logger.info("Worker shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())