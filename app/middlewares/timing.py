import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Uvicorn's access logger uses a formatter that requires ASGI access-log
# fields. TimingMiddleware emits ordinary log records, so use an app logger.
logger = logging.getLogger("bmw_api.requests")


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            if process_time > 2.0:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s"
                )
            else:
                logger.info(
                    f"Processed: {request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s"
                )

            return response
        except Exception:
            process_time = time.time() - start_time
            logger.error(
                f"Failed request: {request.method} {request.url.path} took {process_time:.4f}s"
            )
            raise
