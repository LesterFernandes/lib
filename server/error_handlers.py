import logging
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from services.exceptions import ApplicationError

logger = logging.getLogger(__name__)


def _error_response(
    *, status_code: int, code: str, message: str, details: Any = None
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content=jsonable_encoder({"error": error}))


async def application_error_handler(_: Request, exc: ApplicationError) -> JSONResponse:
    logger.warning("Handled application error [%s]: %s", exc.code, exc.message)
    return _error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    logger.warning("Request validation failed: %s", details)
    return _error_response(
        status_code=422,
        code="validation_error",
        message="Request validation failed.",
        details=details,
    )


async def database_error_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Unhandled database error", exc_info=exc)
    return _error_response(
        status_code=500,
        code="database_error",
        message="The database could not complete the request.",
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled error for %s %s", request.method, request.url.path, exc_info=exc
    )
    return _error_response(
        status_code=500,
        code="internal_error",
        message="An unexpected error occurred.",
    )
