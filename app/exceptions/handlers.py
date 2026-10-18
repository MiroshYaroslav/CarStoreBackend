import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.base import AppException

logger = logging.getLogger("uvicorn.error")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("App error on %s %s: %s", request.method, request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        field = ".".join(str(part) for part in first_error.get("loc", []) if part != "body")
        message = first_error.get("msg", "Validation error")
        detail = f"{field}: {message}" if field else message
    else:
        detail = "Validation error"
    return JSONResponse(status_code=422, content={"detail": detail})


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
