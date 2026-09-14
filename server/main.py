import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import engine
from error_handlers import (
    application_error_handler,
    database_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from routers.books import router as books_router
from routers.loans import router as loans_router
from routers.members import router as members_router
from services.exceptions import ApplicationError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Verify that PostgreSQL is available before serving requests."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.error(
            "Database connection failed; check DATABASE_URL and that the database exists."
        )
        engine.dispose()
        raise

    logger.info("Database connection established.")
    try:
        yield
    finally:
        engine.dispose()
        logger.info("Database engine disposed.")

app = FastAPI(lifespan=lifespan)
app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(SQLAlchemyError, database_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(books_router)
app.include_router(members_router)
app.include_router(loans_router)


@app.get("/")
async def read_root() -> dict[str, str]:
    """A small JSON endpoint to confirm the server is running."""
    return {"message": "Hello from FastAPI!"}

