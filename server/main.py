import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import engine


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


@app.get("/")
async def read_root() -> dict[str, str]:
    """A small JSON endpoint to confirm the server is running."""
    return {"message": "Hello from FastAPI!"}

